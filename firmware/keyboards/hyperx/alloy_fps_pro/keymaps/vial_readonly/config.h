// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include "../raw_compact/config.h"

// The GUI may optimistically show an edit even when firmware rejects it.
// Keep this limitation visible in the USB product AND embedded definition.
#undef PRODUCT
#define PRODUCT "Alloy FPS Pro Vial READ-ONLY"
