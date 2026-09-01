import { useRef, useEffect, useState } from "react";

interface WebGPUCanvasProps {
  shaderCode: string;
  className?: string;
  style?: React.CSSProperties;
  fallbackColors?: [string, string, string];
}

const MAX_DPR = 2;

export function WebGPUCanvas({
  shaderCode,
  className = "",
  style,
  fallbackColors = ["#0c0c0e", "#ff6e41", "#0c0c0e"],
}: WebGPUCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [supported, setSupported] = useState<boolean | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let animId: number;
    let destroyed = false;
    let paused = false;
    let gpuDevice: GPUDevice | null = null;
    let cleanupMouseMove: (() => void) | null = null;
    let cleanupVisibility: (() => void) | null = null;
    let cleanupDeviceLost: (() => void) | null = null;

    async function init() {
      try {
        if (!navigator.gpu) {
          setSupported(false);
          return;
        }

        const adapter = await navigator.gpu.requestAdapter();
        if (!adapter) {
          setSupported(false);
          return;
        }

        const device = await adapter.requestDevice();
        if (destroyed) {
          device.destroy();
          return;
        }
        gpuDevice = device;

        const context = canvas!.getContext("webgpu");
        if (!context) {
          setSupported(false);
          return;
        }

        const format = navigator.gpu.getPreferredCanvasFormat();
        context.configure({ device, format, alphaMode: "premultiplied" });

        const uniformBuffer = device.createBuffer({
          size: 32,
          usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST,
        });

        const shaderModule = device.createShaderModule({ code: shaderCode });

        const pipeline = device.createRenderPipeline({
          layout: "auto",
          vertex: { module: shaderModule, entryPoint: "vs" },
          fragment: {
            module: shaderModule,
            entryPoint: "fs",
            targets: [{ format }],
          },
          primitive: { topology: "triangle-strip" },
        });

        const bindGroup = device.createBindGroup({
          layout: pipeline.getBindGroupLayout(0),
          entries: [{ binding: 0, resource: { buffer: uniformBuffer } }],
        });

        setSupported(true);

        device.lost.then(() => {
          if (!destroyed) setSupported(false);
        });
        cleanupDeviceLost = () => {};

        let mouseX = 0.5;
        let mouseY = 0.5;
        let smoothX = 0.5;
        let smoothY = 0.5;

        const handleMouseMove = (e: MouseEvent) => {
          const rect = canvas!.getBoundingClientRect();
          mouseX = (e.clientX - rect.left) / rect.width;
          mouseY = (e.clientY - rect.top) / rect.height;
        };
        canvas!.addEventListener("mousemove", handleMouseMove);
        cleanupMouseMove = () => canvas!.removeEventListener("mousemove", handleMouseMove);

        const handleVisibility = () => {
          paused = document.hidden;
          if (!paused && !destroyed) animId = requestAnimationFrame(render);
        };
        document.addEventListener("visibilitychange", handleVisibility);
        cleanupVisibility = () => document.removeEventListener("visibilitychange", handleVisibility);

        const startTime = performance.now();

        function render() {
          if (destroyed || paused) return;

          const dpr = Math.min(devicePixelRatio, MAX_DPR);
          const w = canvas!.clientWidth * dpr;
          const h = canvas!.clientHeight * dpr;
          if (canvas!.width !== w || canvas!.height !== h) {
            canvas!.width = w;
            canvas!.height = h;
          }

          smoothX += (mouseX - smoothX) * 0.05;
          smoothY += (mouseY - smoothY) * 0.05;

          const time = (performance.now() - startTime) / 1000;
          const data = new Float32Array([w, h, time, 0, smoothX, smoothY, 0, 0]);
          device.queue.writeBuffer(uniformBuffer, 0, data);

          const encoder = device.createCommandEncoder();
          const pass = encoder.beginRenderPass({
            colorAttachments: [
              {
                view: context!.getCurrentTexture().createView(),
                loadOp: "clear",
                storeOp: "store",
                clearValue: { r: 0, g: 0, b: 0, a: 1 },
              },
            ],
          });
          pass.setPipeline(pipeline);
          pass.setBindGroup(0, bindGroup);
          pass.draw(4);
          pass.end();
          device.queue.submit([encoder.finish()]);

          animId = requestAnimationFrame(render);
        }

        render();
      } catch {
        setSupported(false);
      }
    }

    init();

    return () => {
      destroyed = true;
      cancelAnimationFrame(animId);
      cleanupMouseMove?.();
      cleanupVisibility?.();
      cleanupDeviceLost?.();
      gpuDevice?.destroy();
    };
  }, [shaderCode]);

  const fallbackStyle: React.CSSProperties = {
    background: `linear-gradient(135deg, ${fallbackColors[0]}, ${fallbackColors[1]}, ${fallbackColors[2]})`,
    backgroundSize: "400% 400%",
    ...style,
  };

  if (supported === false) {
    return (
      <div
        className={`${className} animate-gradient-shift`}
        style={fallbackStyle}
      />
    );
  }

  return (
    <canvas
      ref={canvasRef}
      className={className}
      style={{ opacity: supported === null ? 0 : 1, transition: "opacity 0.5s", ...style }}
    />
  );
}
