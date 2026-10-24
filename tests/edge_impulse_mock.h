#pragma once

#include <stddef.h>

#define EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE 3
#define EI_CLASSIFIER_LABEL_COUNT 5

typedef struct {
  size_t total_length;
} signal_t;

typedef struct {
  const char* label;
  float value;
} ei_classification_t;

typedef struct {
  ei_classification_t classification[EI_CLASSIFIER_LABEL_COUNT];
} ei_impulse_result_t;

enum EI_IMPULSE_ERROR {
  EI_IMPULSE_OK = 0
};

namespace numpy {
inline int signal_from_buffer(float*, size_t length, signal_t* signal) {
  signal->total_length = length;
  return 0;
}
}

inline EI_IMPULSE_ERROR run_classifier(signal_t*, ei_impulse_result_t* result, bool) {
  static const char* labels[EI_CLASSIFIER_LABEL_COUNT] = {
    "NORMAL", "COOKING_FUMES", "GAS_DANGER", "HEAT_ANOMALY", "GAS_HEAT_EMERGENCY"
  };
  for (size_t i = 0; i < EI_CLASSIFIER_LABEL_COUNT; ++i) {
    result->classification[i].label = labels[i];
    result->classification[i].value = (i == 0) ? 1.0f : 0.0f;
  }
  return EI_IMPULSE_OK;
}
