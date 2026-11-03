#ifndef ALIN_FONT_RENDERER_H
#define ALIN_FONT_RENDERER_H

#include "alin_emotion.h"

namespace alin {

class FontRenderer : public IEmotionRenderer {
public:
    const char* name() const override { return "font"; }

    bool Init(lv_obj_t* parent, int width, int height) override;
    void Deinit() override;
    void OnEmotionChanged(Emotion emotion) override;
    void Update(uint32_t dt_ms) override;
    void SetVisible(bool visible) override;

private:
    lv_obj_t* label_ = nullptr;
};

}

#endif
