// Gradiente animato con ShaderGradient (MIT, ruucm). Il tempo non scorre da solo:
// rendi.py chiama window.rendi(t) e la pagina disegna il fotogramma al tempo t (secondi).
import React, { useEffect } from "react";
import { createRoot } from "react-dom/client";
import { useThree } from "@react-three/fiber";
import { ShaderGradientCanvas, ShaderGradient } from "@shadergradient/react";

const q = new URLSearchParams(location.search);
const num = (k, d) => (q.has(k) && isFinite(parseFloat(q.get(k))) ? parseFloat(q.get(k)) : d);
const col = (k, d) => { const v = (q.get(k) || "").replace(/^#?/, "#"); return /^#[0-9a-fA-F]{6}$/.test(v) ? v : d; };
const W = num("w", 1280), H = num("h", 720), T0 = num("t", 0);
const tipo = ["plane", "sphere", "waterPlane"].includes(q.get("tipo")) ? q.get("tipo") : "plane";
const velocita = num("velocita", 0.4);
document.body.style.width = W + "px";
document.body.style.height = H + "px";

let stato = null;
function imposta(t) {
  // uTime è l'orologio dello shader: lo impostiamo a mano su ogni materiale di ShaderGradient.
  let n = 0;
  stato.scene.traverse((o) => {
    const u = o.material && o.material.userData && o.material.userData.uTime;
    if (u) { u.value = t; n++; }
  });
  return n;
}
const dueFrame = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
window.rendi = async (t) => {
  const n = imposta(t);
  stato.gl.render(stato.scene, stato.camera);
  await dueFrame();
  return n;
};

function Ponte() {
  const s = useThree();
  useEffect(() => {
    stato = s;
    let tentativi = 0;
    const prova = async () => {
      const n = imposta(T0);
      if (n > 0) { await dueFrame(); window.__pronto = true; }
      else if (tentativi++ < 300) setTimeout(prova, 20);
      else window.__errore = "nessun materiale ShaderGradient trovato";
    };
    prova();
  }, [s]);
  return null;
}

createRoot(document.getElementById("radice")).render(
  <ShaderGradientCanvas style={{ width: W + "px", height: H + "px" }} pixelDensity={1} lazyLoad={false}
                        preserveDrawingBuffer={true} pointerEvents="none">
    <ShaderGradient
      control="props" animate="off" uTime={T0} uSpeed={velocita} type={tipo}
      color1={col("colore1", "#ff5005")} color2={col("colore2", "#dbba95")} color3={col("colore3", "#d0bce1")}
      uStrength={num("forza", 4)} uDensity={num("densita", 1.3)} uFrequency={5.5} uAmplitude={1}
      positionX={-1.4} positionY={0} positionZ={0} rotationX={0} rotationY={10} rotationZ={50}
      cAzimuthAngle={180} cPolarAngle={90} cDistance={3.6} cameraZoom={1}
      lightType="3d" brightness={num("luminosita", 1.2)} grain="off" reflection={0.1} wireframe={false}
    />
    <Ponte />
  </ShaderGradientCanvas>
);
window.addEventListener("error", (e) => { window.__errore = String(e.message || e); });
