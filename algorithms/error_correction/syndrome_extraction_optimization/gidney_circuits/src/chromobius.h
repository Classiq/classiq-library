#ifndef _CHROMOBIUS_H
#define _CHROMOBIUS_H
/// WARNING: THE chromobius C++ API MAKES NO COMPATIBILITY GUARANTEES.
/// It may change arbitrarily and catastrophically from minor version to minor version.
/// If you need a stable API, use chromobius's Python API.
#include "chromobius/commands/main_all.h"
#include "chromobius/commands/main_benchmark.h"
#include "chromobius/commands/main_describe_decoder.h"
#include "chromobius/commands/main_predict.h"
#include "chromobius/datatypes/atomic_error.h"
#include "chromobius/datatypes/color_basis.h"
#include "chromobius/datatypes/conf.h"
#include "chromobius/datatypes/rgb_edge.h"
#include "chromobius/decode/decoder.h"
#include "chromobius/decode/matcher_interface.h"
#include "chromobius/decode/pymatcher.h"
#include "chromobius/graph/charge_graph.h"
#include "chromobius/graph/choose_rgb_reps.h"
#include "chromobius/graph/collect_atomic_errors.h"
#include "chromobius/graph/collect_composite_errors.h"
#include "chromobius/graph/collect_nodes.h"
#include "chromobius/graph/drag_graph.h"
#include "chromobius/graph/euler_tours.h"
#endif
