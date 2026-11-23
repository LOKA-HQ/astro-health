import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

// Realistic human body (CC0 base mesh, Grab3D light version).
const MODEL_URL = '/models/man-base-light.glb';
// Target height of the figure inside the viewport, in scene units.
const TARGET_HEIGHT = 3.4;
const FEET_Y = -1.55;

function makeGlowDiscTexture(isLight) {
  // Soft radial glow pooled on the floor under the figure.
  const size = 256;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  const grad = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  grad.addColorStop(0, isLight ? 'rgba(13, 148, 136, 0.35)' : 'rgba(88, 216, 208, 0.55)');
  grad.addColorStop(0.5, isLight ? 'rgba(13, 148, 136, 0.12)' : 'rgba(88, 216, 208, 0.18)');
  grad.addColorStop(1, isLight ? 'rgba(13, 148, 136, 0)' : 'rgba(88, 216, 208, 0)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, size, size);
  return new THREE.CanvasTexture(canvas);
}

function BodyModel({ hr = 72, t = null, theme = 'dark' }) {
  const mount = useRef(null);
  const hrRef = useRef(hr);
  hrRef.current = hr;
  const [status, setStatus] = useState('loading'); // loading | ready | error

  useEffect(() => {
    const el = mount.current;
    if (!el) return;
    // Accent colors: bright cyan on dark, deep teal on light so the
    // hologram frame stays readable in both themes.
    const isLight = theme === 'light';
    const accent = isLight ? 0x0d9488 : 0x55e0d3;
    setStatus('loading');
    let renderer;
    let pmrem;
    let frame;
    let disposed = false;
    const clock = new THREE.Clock();

    try {
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setSize(el.clientWidth, el.clientHeight);
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.05;
      el.appendChild(renderer.domElement);

      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(35, el.clientWidth / el.clientHeight, 0.1, 100);
      camera.position.set(0, 0.2, 6.3);

      // Image-based lighting: PBR skin and cloth need an environment to read
      // as realistic instead of flat plastic. Kept dim so the key light
      // shapes the form instead of washing it out.
      pmrem = new THREE.PMREMGenerator(renderer);
      scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
      scene.environmentIntensity = 0.55;

      // Lighting: soft key from the front, cool rim from behind, low fill.
      scene.add(new THREE.HemisphereLight(0xbfd9e8, 0x0a121c, 0.7));
      const key = new THREE.DirectionalLight(0xffffff, 1.5);
      key.position.set(2.5, 4, 4);
      scene.add(key);
      const rim = new THREE.PointLight(accent, 25, 0, 1.8);
      rim.position.set(-3, 2, -3);
      scene.add(rim);

      const group = new THREE.Group();
      scene.add(group);

      // Ground glow disc under the feet.
      const disc = new THREE.Mesh(
        new THREE.CircleGeometry(1.5, 48),
        new THREE.MeshBasicMaterial({
          map: makeGlowDiscTexture(isLight),
          transparent: true,
          depthWrite: false,
        }),
      );
      disc.rotation.x = -Math.PI / 2;
      disc.position.y = FEET_Y;
      group.add(disc);

      // Orbital ring, kept from the previous hologram frame.
      const ring = new THREE.Mesh(
        new THREE.TorusGeometry(1.7, 0.008, 8, 100),
        new THREE.MeshBasicMaterial({
          color: isLight ? 0x0f766e : 0x2d778b,
          transparent: true,
          opacity: 0.55,
        }),
      );
      ring.rotation.x = 1.1;
      group.add(ring);

      // Heart pulse: glow sphere + light, placed at the chest once the
      // model loads and its bounding box is known.
      const heartGlow = new THREE.Mesh(
        new THREE.SphereGeometry(0.09, 24, 18),
        new THREE.MeshBasicMaterial({ color: accent, transparent: true, opacity: 0.85 }),
      );
      heartGlow.visible = false;
      group.add(heartGlow);
      const heartLight = new THREE.PointLight(accent, 0, 2.5, 1.8);
      group.add(heartLight);

      // Monitored-system markers orbiting the figure.
      const dotMat = new THREE.MeshBasicMaterial({ color: accent });
      for (let i = 0; i < 6; i++) {
        const a = (i * Math.PI) / 3;
        const dot = new THREE.Mesh(new THREE.SphereGeometry(0.045, 12, 10), dotMat);
        dot.position.set(Math.cos(a) * 1.35, Math.sin(a) * 1.1, 0.2);
        group.add(dot);
      }

      const loader = new GLTFLoader();
      loader.load(
        MODEL_URL,
        (gltf) => {
          if (disposed) return;
          const model = gltf.scene;
          // Auto-fit: scale to target height, center horizontally, feet on the disc.
          const box = new THREE.Box3().setFromObject(model);
          const size = new THREE.Vector3();
          const center = new THREE.Vector3();
          box.getSize(size);
          box.getCenter(center);
          const scale = TARGET_HEIGHT / size.y;
          model.scale.setScalar(scale);
          model.position.set(-center.x * scale, FEET_Y - box.min.y * scale, -center.z * scale);
          group.add(model);
          // Chest anchor from the fitted bounding box: ~72% of height,
          // slightly to the figure's left, just in front of the torso.
          const chestY = FEET_Y + TARGET_HEIGHT * 0.72;
          const chestX = -center.x * scale + size.x * scale * 0.06;
          const chestZ = -center.z * scale + (box.max.z - center.z) * scale + 0.05;
          heartGlow.position.set(chestX, chestY, chestZ);
          heartLight.position.set(chestX, chestY, chestZ + 0.25);
          heartGlow.visible = true;
          setStatus('ready');
        },
        undefined,
        () => {
          if (!disposed) setStatus('error');
        },
      );

      const resize = () => {
        if (!el.clientWidth) return;
        camera.aspect = el.clientWidth / el.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(el.clientWidth, el.clientHeight);
      };
      window.addEventListener('resize', resize);

      const animate = () => {
        frame = requestAnimationFrame(animate);
        const t = clock.getElapsedTime();
        group.rotation.y = Math.sin(t * 0.25) * 0.18;
        // Heartbeat pulse synced to resting heart rate.
        const beat = Math.sin((t * hrRef.current) / 12);
        heartGlow.scale.setScalar(1 + 0.18 * beat);
        heartLight.intensity = 6 + 5 * beat;
        ring.rotation.z = t * 0.05;
        renderer.render(scene, camera);
      };
      animate();

      return () => {
        disposed = true;
        cancelAnimationFrame(frame);
        window.removeEventListener('resize', resize);
        pmrem.dispose();
        renderer.dispose();
        el.innerHTML = '';
      };
    } catch (e) {
      setStatus('error');
      return undefined;
    }
  }, [theme]);

  return (
    <div className="body-model">
      <div className="model-canvas" ref={mount} />
      <div className="model-tag">{t?.bodyTag || 'CREW BIOMETRIC · DEMO'}</div>
      {status === 'loading' && (
        <div className="model-fallback">{t?.bodyLoading || 'LOADING BODY MODEL…'}</div>
      )}
      {status === 'error' && (
        <div className="model-fallback">
          {t?.bodyUnavailable || '3D rendering unavailable'}
          <br />
          <span>{t?.bodyProfile || 'CREW BIOMETRIC PROFILE'}</span>
        </div>
      )}
      <div className="model-legend">
        <span>●</span> {t?.bodySystems || '6 monitored systems'}
      </div>
    </div>
  );
}

export default BodyModel;
