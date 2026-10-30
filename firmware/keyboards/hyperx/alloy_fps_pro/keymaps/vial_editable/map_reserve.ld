/* No code/data load image may overlap the two map banks. */
ASSERT(__flash0_free__ <= 0x7000, "application overlaps reserved Vial maps")
