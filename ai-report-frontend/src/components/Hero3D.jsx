import { Canvas, useFrame } from "@react-three/fiber";
import { Float, MeshDistortMaterial, Sphere, Stars } from "@react-three/drei";
import { useRef } from "react";

function Orb() {
  const orbRef = useRef(null);

  useFrame((state) => {
    if (!orbRef.current) {
      return;
    }
    orbRef.current.rotation.x = state.clock.elapsedTime * 0.15;
    orbRef.current.rotation.y = state.clock.elapsedTime * 0.2;
  });

  return (
    <Float speed={1.5} rotationIntensity={1.2} floatIntensity={2}>
      <Sphere ref={orbRef} args={[1.3, 128, 128]} position={[0, 0, 0]}>
        <MeshDistortMaterial
          color="#6a8dff"
          emissive="#5f3eff"
          emissiveIntensity={0.6}
          distort={0.45}
          speed={2.2}
          roughness={0.08}
          metalness={0.55}
        />
      </Sphere>
    </Float>
  );
}

export default function Hero3D() {
  return (
    <div className="hero-canvas">
      <Canvas camera={{ position: [0, 0, 4.5], fov: 55 }}>
        <ambientLight intensity={0.7} />
        <pointLight color="#6ea8fe" intensity={16} position={[3, 2, 2]} />
        <pointLight color="#8b5cf6" intensity={13} position={[-3, -2, 1]} />
        <Stars radius={90} depth={45} count={2200} factor={3} saturation={0} fade speed={0.75} />
        <Orb />
      </Canvas>
    </div>
  );
}
