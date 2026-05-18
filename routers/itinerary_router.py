from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from routers.auth import get_current_user
from datetime import datetime
from io import BytesIO
import os
import models, schemas

# ─── ReportLab Imports ───────────────────────────────────────────────────────
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

router = APIRouter(prefix="/api/itinerary", tags=["Itinerary"])


# ─────────────────────────────────────────────────────────────────────────────
#  PDF EXPORT — HELPERS
# ─────────────────────────────────────────────────────────────────────────────

# ----- Color palette ---------------------------------------------------------
_BLUE       = colors.HexColor("#004AAD")
_BLUE_DARK  = colors.HexColor("#1565C0")
_LIME       = colors.HexColor("#C0F11C")
_WHITE      = colors.white
_BLACK      = colors.HexColor("#1E1E1E")
_LIGHT_BG   = colors.HexColor("#F0F5FF")
_MID_BG     = colors.HexColor("#E8F0FD")
_GRAY       = colors.HexColor("#6B7280")
_LIGHT_GRAY = colors.HexColor("#D1D9E6")
_AMBER      = colors.HexColor("#B45309")

PAGE_W, PAGE_H = A4

# ----- Font registration (Poppins as Plus Jakarta Sans substitute) -----------
def _register_fonts():
    """Register Poppins as 'Jakarta' font family. Safe to call multiple times."""
    font_dir = "/usr/share/fonts/truetype/google-fonts"
    try:
        pdfmetrics.registerFont(TTFont("Jakarta",        f"{font_dir}/Poppins-Regular.ttf"))
        pdfmetrics.registerFont(TTFont("Jakarta-Bold",   f"{font_dir}/Poppins-Bold.ttf"))
        pdfmetrics.registerFont(TTFont("Jakarta-Medium", f"{font_dir}/Poppins-Medium.ttf"))
        pdfmetrics.registerFont(TTFont("Jakarta-Light",  f"{font_dir}/Poppins-Light.ttf"))
        pdfmetrics.registerFontFamily("Jakarta", normal="Jakarta", bold="Jakarta-Bold")
    except Exception:
        pass  # Fonts already registered or not available — falls back to Helvetica


# ----- Asset paths -----------------------------------------------------------
_ASSET_DIR    = os.path.join(os.path.dirname(__file__), "assets")
_LOGO_WHITE   = os.path.join(_ASSET_DIR, "textlogo-white.png")  # white logo on transparent bg
_ICON         = os.path.join(_ASSET_DIR, "icon.png")            # square app icon


# ----- Canvas subclass for branded header & footer on every page -------------
def _make_canvas_class(itinerary_title: str, total_hari: int, created_at: str):
    """
    Factory that returns a BandungAjaCanvas class pre-loaded with the current
    itinerary metadata so it can be drawn on every page by ReportLab.
    """

    class BandungAjaCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            canvas.Canvas.__init__(self, *args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self._draw_header_footer(num_pages)
                canvas.Canvas.showPage(self)
            canvas.Canvas.save(self)

        def _draw_header_footer(self, page_count: int):
            self.saveState()
            w, h = A4

            # ── Header background ──────────────────────────────────────────
            self.setFillColor(_BLUE)
            self.rect(0, h - 70 * mm, w, 70 * mm, fill=1, stroke=0)

            # Lime accent bar separating header from content
            self.setFillColor(_LIME)
            self.rect(0, h - 73 * mm, w, 3 * mm, fill=1, stroke=0)

            # ── App icon (top-right corner) ────────────────────────────────
            try:
                icon_size = 14 * mm
                self.drawImage(
                    _ICON,
                    w - 18 * mm, h - 16 * mm,
                    width=icon_size, height=icon_size,
                    preserveAspectRatio=True, mask="auto",
                )
            except Exception:
                pass

            # ── BandungAja text logo (white, top-left) ─────────────────────
            try:
                logo_w = 52 * mm
                logo_h = logo_w * (978 / 6059)   # original aspect ratio
                self.drawImage(
                    _LOGO_WHITE,
                    12 * mm, h - 14 * mm - logo_h,
                    width=logo_w, height=logo_h,
                    preserveAspectRatio=True, mask="auto",
                )
            except Exception:
                # Fallback: just write the name
                self.setFillColor(_WHITE)
                self.setFont("Jakarta-Bold", 11)
                self.drawString(12 * mm, h - 16 * mm, "BandungAja.")

            # ── Itinerary title ────────────────────────────────────────────
            self.setFillColor(_WHITE)
            self.setFont("Jakarta-Bold", 16)
            self.drawString(12 * mm, h - 34 * mm, itinerary_title)

            # ── Meta: hari count · date · traveler type ────────────────────
            self.setFillColor(_LIME)
            self.setFont("Jakarta", 9)
            tanggal = str(created_at).split(" ")[0]
            meta_text = f"\u25cf  {total_hari} Hari    \u25cf  {tanggal}"
            self.drawString(12 * mm, h - 43 * mm, meta_text)

            # ── Decorative dots (bottom-right of header) ───────────────────
            self.setFillColor(_BLUE_DARK)
            for i in range(7):
                self.circle(w - 32 * mm + i * 4.5 * mm, h - 57 * mm, 1.8 * mm, fill=1, stroke=0)

            # ── Footer ────────────────────────────────────────────────────
            footer_h = 12 * mm
            self.setFillColor(_BLACK)
            self.rect(0, 0, w, footer_h, fill=1, stroke=0)

            # Lime top border on footer
            self.setFillColor(_LIME)
            self.rect(0, footer_h, w, 0.8 * mm, fill=1, stroke=0)

            # Footer left text
            self.setFillColor(_WHITE)
            self.setFont("Jakarta", 7)
            self.drawString(12 * mm, 4 * mm, "BandungAja. \u2014 Jelajahi Bandung dengan Mudah")

            # Footer right: page number
            self.setFillColor(_LIME)
            self.setFont("Jakarta-Bold", 7)
            self.drawRightString(
                w - 12 * mm, 4 * mm,
                f"Halaman {self._pageNumber} / {page_count}"
            )

            self.restoreState()

    return BandungAjaCanvas


# ----- Paragraph styles -------------------------------------------------------
def _build_styles() -> dict:
    return {
        "th": ParagraphStyle(
            "th", fontName="Jakarta-Bold", fontSize=8,
            textColor=_WHITE, leading=11,
        ),
        "th_center": ParagraphStyle(
            "th_center", fontName="Jakarta-Bold", fontSize=8,
            textColor=_WHITE, leading=11, alignment=TA_CENTER,
        ),
        "tempat_name": ParagraphStyle(
            "tempat_name", fontName="Jakarta-Bold", fontSize=10,
            textColor=_BLACK, leading=13, spaceAfter=1,
        ),
        "kategori": ParagraphStyle(
            "kategori", fontName="Jakarta", fontSize=7.5,
            textColor=_BLUE, leading=10,
        ),
        "alamat": ParagraphStyle(
            "alamat", fontName="Jakarta", fontSize=8,
            textColor=_GRAY, leading=11,
        ),
        "jam": ParagraphStyle(
            "jam", fontName="Jakarta-Bold", fontSize=9,
            textColor=_BLUE, leading=12, alignment=TA_CENTER,
        ),
        "rating": ParagraphStyle(
            "rating", fontName="Jakarta-Bold", fontSize=8,
            textColor=_AMBER, leading=11, alignment=TA_CENTER,
        ),
        "catatan": ParagraphStyle(
            "catatan", fontName="Jakarta", fontSize=8,
            textColor=colors.HexColor("#374151"), leading=11,
        ),
        "summary_label": ParagraphStyle(
            "summary_label", fontName="Jakarta", fontSize=8,
            textColor=_GRAY, leading=11,
        ),
        "summary_val": ParagraphStyle(
            "summary_val", fontName="Jakarta-Bold", fontSize=10,
            textColor=_BLUE, leading=13,
        ),
        "hari_title": ParagraphStyle(
            "hari_title", fontName="Jakarta-Bold", fontSize=11,
            textColor=_WHITE, leading=14,
        ),
        "hari_count": ParagraphStyle(
            "hari_count", fontName="Jakarta", fontSize=8,
            textColor=_LIME, leading=12, alignment=TA_RIGHT,
        ),
        "footer_note": ParagraphStyle(
            "footer_note", fontName="Jakarta", fontSize=7.5,
            textColor=_GRAY, leading=11, alignment=TA_CENTER,
        ),
        "no": ParagraphStyle(
            "no", fontName="Jakarta-Bold", fontSize=9,
            textColor=_BLACK, leading=12, alignment=TA_CENTER,
        ),
    }


# ----- Core PDF builder -------------------------------------------------------
def _build_pdf(itinerary, jadwal: dict) -> BytesIO:
    """
    Build a beautifully designed A4 itinerary PDF and return it as a BytesIO.

    Args:
        itinerary : SQLAlchemy Itinerary model instance (or any object with
                    .judul, .total_hari, .created_at attributes).
        jadwal    : dict mapping "Hari N" → list of item dicts, each with keys:
                    urutan, jam, catatan, tempat {nama, kategori, alamat, rating}.
    """
    _register_fonts()
    s = _build_styles()

    MARGIN_TOP    = 80 * mm   # must clear the branded header
    MARGIN_BOTTOM = 20 * mm   # must clear the footer
    MARGIN_SIDE   = 14 * mm

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN_SIDE, rightMargin=MARGIN_SIDE,
        topMargin=MARGIN_TOP,   bottomMargin=MARGIN_BOTTOM,
        title=itinerary.judul,
        author="BandungAja.",
    )

    usable_w = PAGE_W - 2 * MARGIN_SIDE
    story    = []

    # ── Summary box ──────────────────────────────────────────────────────────
    total_stops = sum(len(v) for v in jadwal.values())
    col_w = usable_w / 3
    summary_table = Table(
        [
            [
                Paragraph("Total Hari",       s["summary_label"]),
                Paragraph("Total Destinasi",  s["summary_label"]),
                Paragraph("Tanggal Dibuat",   s["summary_label"]),
            ],
            [
                Paragraph(f"{itinerary.total_hari} Hari",  s["summary_val"]),
                Paragraph(f"{total_stops} Tempat",         s["summary_val"]),
                Paragraph(str(itinerary.created_at).split(" ")[0], s["summary_val"]),
            ],
        ],
        colWidths=[col_w] * 3,
    )
    summary_table.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, -1), _LIGHT_BG),
        ("TOPPADDING",     (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 8),
        ("LEFTPADDING",    (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 10),
        ("LINEBELOW",      (0, 0), (-1, 0),  0.5, _LIGHT_GRAY),
        ("LINEAFTER",      (0, 0), (1, -1),  0.5, _LIGHT_GRAY),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 6 * mm))

    # ── Per-day sections ─────────────────────────────────────────────────────
    col_widths = [10 * mm, 68 * mm, 18 * mm, 17 * mm, 50 * mm]

    for hari_key, items in jadwal.items():

        # Day header row
        hari_header = Table(
            [[
                Paragraph(f"  {hari_key}", s["hari_title"]),
                Paragraph(f"{len(items)} Destinasi", s["hari_count"]),
            ]],
            colWidths=[usable_w * 0.72, usable_w * 0.28],
        )
        hari_header.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), _BLUE),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(hari_header)

        # Table: column headers
        table_data = [[
            Paragraph("#",               s["th_center"]),
            Paragraph("Tempat & Alamat", s["th"]),
            Paragraph("Jam",             s["th_center"]),
            Paragraph("Rating",          s["th_center"]),
            Paragraph("Catatan",         s["th"]),
        ]]

        # Table: data rows
        for item in items:
            t = item["tempat"] or {}

            tempat_cell = [
                Paragraph(t.get("nama", "-"),     s["tempat_name"]),
                Paragraph(t.get("kategori", ""),  s["kategori"]),
                Paragraph(t.get("alamat", ""),    s["alamat"]),
            ]

            rating_val  = t.get("rating")
            rating_text = f"\u2605 {rating_val}" if rating_val else "-"

            table_data.append([
                Paragraph(str(item.get("urutan", "")), s["no"]),
                tempat_cell,
                Paragraph(item.get("jam") or "-",     s["jam"]),
                Paragraph(rating_text,                 s["rating"]),
                Paragraph(item.get("catatan") or "-",  s["catatan"]),
            ])

        items_table = Table(table_data, colWidths=col_widths, repeatRows=1)

        row_styles = [
            # Column-header row
            ("BACKGROUND",    (0, 0), (-1, 0),   _BLUE_DARK),
            ("LINEBELOW",     (0, 0), (-1, 0),   1, _LIME),
            # Global padding
            ("TOPPADDING",    (0, 0), (-1, -1),  6),
            ("BOTTOMPADDING", (0, 0), (-1, -1),  6),
            ("LEFTPADDING",   (0, 0), (-1, -1),  6),
            ("RIGHTPADDING",  (0, 0), (-1, -1),  6),
            # Alignment
            ("VALIGN",        (0, 0), (-1, -1),  "MIDDLE"),
            ("ALIGN",         (0, 0), (0, -1),   "CENTER"),
            ("ALIGN",         (2, 0), (3, -1),   "CENTER"),
            # Grid
            ("GRID",          (0, 0), (-1, -1),  0.4, _LIGHT_GRAY),
        ]

        for i in range(1, len(items) + 1):
            bg = _WHITE if (i - 1) % 2 == 0 else _MID_BG
            row_styles.append(("BACKGROUND", (0, i), (-1, i), bg))
            row_styles.append(("BACKGROUND", (0, i), (0, i),  _LIME))  # lime No. cell

        items_table.setStyle(TableStyle(row_styles))
        story.append(items_table)
        story.append(Spacer(1, 5 * mm))

    # ── Closing note ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 3 * mm))
    story.append(HRFlowable(width=usable_w, thickness=0.5, color=_LIGHT_GRAY))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "Dibuat dengan \u2764 menggunakan <b>BandungAja.</b> "
        "\u2014 Aplikasi panduan wisata terbaik untuk menjelajahi Kota Kembang.",
        s["footer_note"],
    ))

    # ── Build ─────────────────────────────────────────────────────────────────
    canvas_class = _make_canvas_class(
        itinerary_title=itinerary.judul,
        total_hari=itinerary.total_hari,
        created_at=itinerary.created_at,
    )
    doc.build(story, canvasmaker=canvas_class)
    buffer.seek(0)
    return buffer


# ─────────────────────────────────────────────────────────────────────────────
#  ROUTER ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/")
def get_itinerary(
    db           : Session     = Depends(get_db),
    current_user : models.User = Depends(get_current_user),
):
    return (
        db.query(models.Itinerary)
        .filter(models.Itinerary.user_id == current_user.id)
        .all()
    )


@router.post("/")
def buat_itinerary(
    judul        : str,
    total_hari   : int,
    db           : Session     = Depends(get_db),
    current_user : models.User = Depends(get_current_user),
):
    itinerary_baru = models.Itinerary(
        user_id    = current_user.id,
        judul      = judul,
        total_hari = total_hari,
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    db.add(itinerary_baru)
    db.commit()
    db.refresh(itinerary_baru)
    return itinerary_baru


@router.get("/{itinerary_id}")
def get_detail_itinerary(
    itinerary_id : int,
    db           : Session     = Depends(get_db),
    current_user : models.User = Depends(get_current_user),
):
    itinerary = db.query(models.Itinerary).filter(
        models.Itinerary.id      == itinerary_id,
        models.Itinerary.user_id == current_user.id,
    ).first()
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary tidak ditemukan")

    item_list = (
        db.query(models.ItineraryItem)
        .filter(models.ItineraryItem.itinerary_id == itinerary_id)
        .order_by(models.ItineraryItem.hari, models.ItineraryItem.urutan)
        .all()
    )

    jadwal = {}
    for item in item_list:
        tempat  = db.query(models.Tempat).filter(models.Tempat.id == item.tempat_id).first()
        hari_key = f"Hari {item.hari}"
        jadwal.setdefault(hari_key, []).append({
            "item_id" : item.id,
            "urutan"  : item.urutan,
            "jam"     : item.jam,
            "catatan" : item.catatan,
            "tempat"  : {
                "id"       : tempat.id,
                "nama"     : tempat.nama,
                "kategori" : tempat.kategori,
                "alamat"   : tempat.alamat,
                "rating"   : tempat.rating,
            } if tempat else None,
        })

    return {
        "id"         : itinerary.id,
        "judul"      : itinerary.judul,
        "total_hari" : itinerary.total_hari,
        "created_at" : itinerary.created_at,
        "jadwal"     : jadwal,
    }


@router.post("/{itinerary_id}/item")
def tambah_item(
    itinerary_id : int,
    tempat_id    : int,
    hari         : int,
    urutan       : int,
    jam          : str  = None,
    catatan      : str  = None,
    db           : Session     = Depends(get_db),
    current_user : models.User = Depends(get_current_user),
):
    itinerary = db.query(models.Itinerary).filter(
        models.Itinerary.id      == itinerary_id,
        models.Itinerary.user_id == current_user.id,
    ).first()
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary tidak ditemukan")

    tempat = db.query(models.Tempat).filter(models.Tempat.id == tempat_id).first()
    if not tempat:
        raise HTTPException(status_code=404, detail="Tempat tidak ditemukan")

    if hari > itinerary.total_hari:
        raise HTTPException(
            status_code=400,
            detail=f"Hari {hari} melebihi total hari itinerary ({itinerary.total_hari} hari)",
        )

    item_baru = models.ItineraryItem(
        itinerary_id = itinerary_id,
        tempat_id    = tempat_id,
        hari         = hari,
        urutan       = urutan,
        jam          = jam,
        catatan      = catatan,
    )
    db.add(item_baru)
    db.commit()
    db.refresh(item_baru)
    return {"message": f"{tempat.nama} berhasil ditambahkan ke Hari {hari}"}


@router.delete("/{itinerary_id}")
def hapus_itinerary(
    itinerary_id : int,
    db           : Session     = Depends(get_db),
    current_user : models.User = Depends(get_current_user),
):
    itinerary = db.query(models.Itinerary).filter(
        models.Itinerary.id      == itinerary_id,
        models.Itinerary.user_id == current_user.id,
    ).first()
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary tidak ditemukan")

    db.query(models.ItineraryItem)\
      .filter(models.ItineraryItem.itinerary_id == itinerary_id)\
      .delete()
    db.delete(itinerary)
    db.commit()
    return {"message": f"Itinerary '{itinerary.judul}' berhasil dihapus"}


@router.delete("/{itinerary_id}/item/{item_id}")
def hapus_item(
    itinerary_id : int,
    item_id      : int,
    db           : Session     = Depends(get_db),
    current_user : models.User = Depends(get_current_user),
):
    itinerary = db.query(models.Itinerary).filter(
        models.Itinerary.id      == itinerary_id,
        models.Itinerary.user_id == current_user.id,
    ).first()
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary tidak ditemukan")

    item = db.query(models.ItineraryItem).filter(
        models.ItineraryItem.id           == item_id,
        models.ItineraryItem.itinerary_id == itinerary_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")

    db.delete(item)
    db.commit()
    return {"message": f"Item berhasil dihapus dari Hari {item.hari}"}


# ─────────────────────────────────────────────────────────────────────────────
#  EXPORT PDF  ←  endpoint yang diperbarui
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{itinerary_id}/export-pdf")
def export_itinerary_pdf(
    itinerary_id : int,
    db           : Session     = Depends(get_db),
    current_user : models.User = Depends(get_current_user),
):
    """
    Ekspor itinerary sebagai PDF A4 berdesain dengan branding BandungAja.
    Mengembalikan file PDF sebagai streaming download.
    """
    # 1. Ambil itinerary
    itinerary = db.query(models.Itinerary).filter(
        models.Itinerary.id      == itinerary_id,
        models.Itinerary.user_id == current_user.id,
    ).first()
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary tidak ditemukan")

    # 2. Ambil semua item, susun per hari
    item_list = (
        db.query(models.ItineraryItem)
        .filter(models.ItineraryItem.itinerary_id == itinerary_id)
        .order_by(models.ItineraryItem.hari, models.ItineraryItem.urutan)
        .all()
    )
    if not item_list:
        raise HTTPException(status_code=404, detail="Itinerary tidak memiliki destinasi")

    jadwal: dict = {}
    for item in item_list:
        tempat   = db.query(models.Tempat).filter(models.Tempat.id == item.tempat_id).first()
        hari_key = f"Hari {item.hari}"
        jadwal.setdefault(hari_key, []).append({
            "urutan"  : item.urutan,
            "jam"     : item.jam,
            "catatan" : item.catatan,
            "tempat"  : {
                "nama"     : tempat.nama,
                "kategori" : tempat.kategori,
                "alamat"   : tempat.alamat,
                "rating"   : tempat.rating,
            } if tempat else None,
        })

    # 3. Build PDF
    pdf_buffer = _build_pdf(itinerary, jadwal)

    # 4. Stream ke client
    safe_filename = itinerary.judul.replace(" ", "_").replace("/", "-")
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}.pdf"'
        },
    )
