"""
Seequa Chameleon Silkscreen Formatter

- For U* footprints:
    - 'seq_silkscreen' field:
        * ensure 'seq_silkscreen' field exists (PCB_FIELD)
        * if Value field starts with '74' and 'seq_silkscreen' is blank, set field to Value[2:]
        * make 'seq_silkscreen' field visible on front silkscreen layer with specified size/thickness
        * auto-place BELOW the pads-only bounding box (x centered, y = pad_bbox_bottom + offset)
          but ONLY when the field still looks "uninitialized":
            - its current position equals the footprint anchor position, AND
            - its text angle is 0 (so we don't stomp intentional rotations)
    - Reference (U value)
        * make visible on front silkscreen layer with specified size/thickness
        * center justification
        * force text angle to 0
        * place at pads-only center

- For non-U footprints:
    - Use 'seq_silkscreen' field as a above, if it exists
    - Otherwise use 'Reference' field.

Notes:
  - KiCad 9+ only
"""

import pcbnew

SILK_FIELD_NAME = "seq_silkscreen"
VALUE_PREFIX = "74"
USE_BACK_SILK_FOR_SEQ = False  # False => F.SilkS, True => B.SilkS

MAIN_TEXT_W_MM = 1.35
MAIN_TEXT_H_MM = 1.35
MAIN_THICK_MM = 0.27

# Distance below pads bbox bottom for seq_silkscreen placement:
MAIN_BELOW_OFFSET_MM = 2.0

# Only auto-move seq_silkscreen if it looks "uninitialized":
AUTO_MOVE_REQUIRES_ANGLE_ZERO = True
 
# ---- UXXX Reference formatting ----
REF_TEXT_W_MM = 1.0
REF_TEXT_H_MM = 1.0
REF_THICK_MM = 0.15

def _mm(x: float) -> int:
    return pcbnew.FromMM(x)

def _is_blank(s: str) -> bool:
    return s is None or str(s).strip() == ""

def _set_status(text: str):
    print(text)
    if hasattr(pcbnew, "GetFrame"):
        try:
            frame = pcbnew.GetFrame()
            if frame is not None and hasattr(frame, "SetStatusText"):
                frame.SetStatusText(text)
        except Exception:
            pass

def _get_field_or_none(fp: pcbnew.FOOTPRINT, name: str):
    try:
        f = fp.GetFieldByName(name)
        return f if f is not None else None
    except Exception:
        return None

def _is_field_blank_or_none(fp: pcbnew.FOOTPRINT, name: str) -> bool:
    
    try:
        f = fp.GetFieldByName(name)
        if f is None:
            return True
        text = f.GetText()
        return _is_blank(text) or text == "~"
    except Exception:
        return True


def _ensure_field(fp: pcbnew.FOOTPRINT, name: str) -> pcbnew.PCB_FIELD:
    f = _get_field_or_none(fp, name)
    if f is not None:
        return f

    nf = pcbnew.PCB_FIELD(fp)
    nf.SetName(name)
    nf.SetText("")
    fp.AddField(nf)
    return nf

def _center_justify_text(text_obj):
    if hasattr(text_obj, "SetHorizJustify"):
        text_obj.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    else:
        text_obj.SetHorizJustification(pcbnew.GR_TEXT_H_ALIGN_CENTER)

    if hasattr(text_obj, "SetVertJustify"):
        text_obj.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    else:
        text_obj.SetVertJustification(pcbnew.GR_TEXT_V_ALIGN_CENTER)

def _pads_bbox_minmax(fp: pcbnew.FOOTPRINT):
    """Union of pad bounding boxes (pads only). Returns (minx, miny, maxx, maxy)."""
    pads = list(fp.Pads())
    if not pads:
        bb = fp.GetBoundingBox()
        return bb.GetX(), bb.GetY(), bb.GetRight(), bb.GetBottom()

    bb = pads[0].GetBoundingBox()
    minx = bb.GetX()
    miny = bb.GetY()
    maxx = bb.GetRight()
    maxy = bb.GetBottom()

    for p in pads[1:]:
        pb = p.GetBoundingBox()
        minx = min(minx, pb.GetX())
        miny = min(miny, pb.GetY())
        maxx = max(maxx, pb.GetRight())
        maxy = max(maxy, pb.GetBottom())

    return minx, miny, maxx, maxy

def _pads_only_center(fp: pcbnew.FOOTPRINT) -> pcbnew.VECTOR2I:
    minx, miny, maxx, maxy = _pads_bbox_minmax(fp)
    return pcbnew.VECTOR2I((minx + maxx) // 2, (miny + maxy) // 2)

def _pads_only_bottom_center(fp: pcbnew.FOOTPRINT, below_offset_mm: float) -> pcbnew.VECTOR2I:
    minx, _miny, maxx, maxy = _pads_bbox_minmax(fp)
    cx = (minx + maxx) // 2
    cy = maxy + _mm(below_offset_mm)
    return pcbnew.VECTOR2I(cx, cy)

def _apply_main_style(field: pcbnew.PCB_FIELD, target_layer: int, visible: bool):
    field.SetVisible(bool(visible))
    if not visible:
        return

    field.SetLayer(target_layer)
    field.SetTextSize(pcbnew.VECTOR2I(_mm(MAIN_TEXT_W_MM), _mm(MAIN_TEXT_H_MM)))
    field.SetTextThickness(_mm(MAIN_THICK_MM))

    # ensure position centering uses a centered anchor
    _center_justify_text(field)

def _set_text_angle_zero(text_obj) -> bool:
    if not hasattr(text_obj, "SetTextAngle"):
        return False

    # Prefer explicit EDA_ANGLE if available
    if hasattr(pcbnew, "EDA_ANGLE"):
        try:
            text_obj.SetTextAngle(pcbnew.EDA_ANGLE(0))
            return True
        except Exception:
            pass

        for unit_name in ("DEGREES_T", "TENTHS_OF_A_DEGREE_T", "RADIANS_T"):
            if hasattr(pcbnew, unit_name):
                try:
                    unit = getattr(pcbnew, unit_name)
                    text_obj.SetTextAngle(pcbnew.EDA_ANGLE(0, unit))
                    return True
                except Exception:
                    pass

    # last resort
    try:
        text_obj.SetTextAngle(0)
        return True
    except Exception:
        return False

def _is_text_angle_zero(text_obj) -> bool:
    if not hasattr(text_obj, "GetTextAngle"):
        return False

    try:
        ang = text_obj.GetTextAngle()
    except Exception:
        return False

    for meth in ("AsDegrees", "AsTenthsOfADegree", "AsTenthsOfDegrees"):
        if hasattr(ang, meth):
            try:
                return int(getattr(ang, meth)()) == 0
            except Exception:
                pass

    try:
        return int(ang) == 0
    except Exception:
        pass

    try:
        return str(ang).strip() in ("0", "0.0")
    except Exception:
        return False

def _should_auto_place_field(fp: pcbnew.FOOTPRINT, silk_field: pcbnew.PCB_FIELD) -> bool:
    """Auto-place only if field is at footprint anchor and (optionally) angle==0."""
    try:
        cur = silk_field.GetPosition()
    except Exception:
        return False

    # KiCad default for newly-added/untouched fields tends to be footprint anchor.
    try:
        anchor = fp.GetPosition()
    except Exception:
        anchor = None

    if anchor is None:
        return False

    if cur.x != anchor.x or cur.y != anchor.y:
        return False

    if AUTO_MOVE_REQUIRES_ANGLE_ZERO:
        return _is_text_angle_zero(silk_field)

    return True

def _format_and_center_reference(fp: pcbnew.FOOTPRINT) -> bool:
    ref_field = _get_field_or_none(fp, "Reference")
    if ref_field is None:
        return False

    ref_field.SetVisible(True)
    ref_field.SetTextSize(pcbnew.VECTOR2I(_mm(REF_TEXT_W_MM), _mm(REF_TEXT_H_MM)))
    ref_field.SetTextThickness(_mm(REF_THICK_MM))
    _center_justify_text(ref_field)
    _set_text_angle_zero(ref_field)
    ref_field.SetPosition(_pads_only_center(fp))
    return True

def _hide_reference(fp: pcbnew.FOOTPRINT) -> bool:
    ref_field = _get_field_or_none(fp, "Reference")
    if ref_field is None:
        return False

    ref_field.SetVisible(False)

def _handle_u(fp: pcbnew.FOOTPRINT, seq_layer: int) -> bool:
    val = (fp.GetValue() or "").strip()
    existing_silk = _get_field_or_none(fp, SILK_FIELD_NAME)

    # Create 'seq_silkscreen' field if it doesn't exist
    if existing_silk is None:
        silk_field = _ensure_field(fp, SILK_FIELD_NAME)
    else:
        silk_field = existing_silk

    if val.startswith(VALUE_PREFIX) and _is_blank(silk_field.GetText()):
        silk_field.SetText(val[len(VALUE_PREFIX):])

    _apply_main_style(silk_field, seq_layer, visible=True)

    # Auto-place below pads bbox only if it still looks uninitialized
    if _should_auto_place_field(fp, silk_field):
        silk_field.SetPosition(_pads_only_bottom_center(fp, MAIN_BELOW_OFFSET_MM))

    # Format the reference field (u-number)
    try:
        _format_and_center_reference(fp)
    except Exception:
        pass

def _handle_other(fp: pcbnew.FOOTPRINT, seq_layer: int) -> bool:
    # Use silkscreen field if it exists and is not blank, otherwise use reference field
    if _is_field_blank_or_none(fp, SILK_FIELD_NAME):
        silk_field = _get_field_or_none(fp, "Reference")
    else:
        silk_field = _get_field_or_none(fp, SILK_FIELD_NAME)
        _hide_reference(fp)

    if silk_field is not None:
        _apply_main_style(silk_field, seq_layer, visible=True)

class SeequaChameleonSilkscreenHelper(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Sequa Chameleon Silkscreen Helper"
        self.category = "Modify PCB"
        self.description = (
            "Format silkscreen based on custom silkscreen field."
        )
        self.show_toolbar_button = True

    def Run(self):
        board = pcbnew.GetBoard()
        if board is None:
            _set_status("Silkscreen helper: no board open.")
            return

        seq_layer = pcbnew.B_SilkS if USE_BACK_SILK_FOR_SEQ else pcbnew.F_SilkS

        for fp in board.GetFootprints():
            ref = (fp.GetReference() or "").strip()
            
            if ref.upper().startswith("U"):
                _handle_u(fp, seq_layer)
            else:
                _handle_other(fp, seq_layer)


        pcbnew.Refresh()


# Main plugin registration
SeequaChameleonSilkscreenHelper().register()
