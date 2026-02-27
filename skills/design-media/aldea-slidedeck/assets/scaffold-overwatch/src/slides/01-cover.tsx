import { SlideWrapper } from "../components/layout/SlideWrapper";
import { CenterLayout } from "../components/layout/CenterLayout";
import { StaggeredAnimation } from "../components/interactions/StaggeredAnimation";
import { AnimatedItem } from "../components/interactions/AnimatedItem";
import { WebGPUCanvas } from "../components/graphics/WebGPUCanvas";
import shaderCode from "../components/graphics/shaders/lava-nebula.wgsl?raw";

export default function CoverSlide() {
  return (
    <SlideWrapper mode="dark" className="p-0">
      {/* Shader background */}
      <WebGPUCanvas
        shaderCode={shaderCode}
        className="absolute inset-0 w-full h-full"
        fallbackColors={["#0c0c0e", "#ff6e41", "#0c0c0e"]}
      />

      {/* Dark gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#0a0500]/30 to-[#0a0500]/80" />

      {/* Content */}
      <CenterLayout className="relative z-10 px-[64px]">
        <StaggeredAnimation stagger={0.15} delay={0.3}>
          <AnimatedItem variant="slideUp">
            <p
              className="text-[20px] tracking-[0.3em] uppercase font-semibold mb-6"
              style={{ fontFamily: "var(--font-body)", color: "var(--color-orange)" }}
            >
              Presentation Title
            </p>
          </AnimatedItem>

          <AnimatedItem variant="slideUp">
            <h1
              className="text-[140px] leading-[0.85] tracking-[-0.02em] uppercase"
              style={{ fontFamily: "var(--font-heading)", color: "var(--color-white)" }}
            >
              Your Deck
            </h1>
          </AnimatedItem>

          <AnimatedItem variant="fade">
            <p
              className="text-[24px] mt-8 max-w-[600px] leading-[1.6]"
              style={{ fontFamily: "var(--font-body)", color: "rgba(203, 213, 225, 0.8)" }}
            >
              A brief subtitle or tagline for your presentation goes here.
            </p>
          </AnimatedItem>
        </StaggeredAnimation>
      </CenterLayout>
    </SlideWrapper>
  );
}
