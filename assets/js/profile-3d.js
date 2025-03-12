// Initialize Three.js scene
import * as THREE from 'https://cdn.skypack.dev/three@0.136.0';
import { OrbitControls } from 'https://cdn.skypack.dev/three@0.136.0/examples/jsm/controls/OrbitControls.js';

// Scene setup
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });

// Skills cube
class SkillsCube {
    constructor() {
        this.geometry = new THREE.BoxGeometry(2, 2, 2);
        this.materials = [
            new THREE.MeshPhongMaterial({ map: this.createTextTexture('Python') }),
            new THREE.MeshPhongMaterial({ map: this.createTextTexture('React') }),
            new THREE.MeshPhongMaterial({ map: this.createTextTexture('Node.js') }),
            new THREE.MeshPhongMaterial({ map: this.createTextTexture('MongoDB') }),
            new THREE.MeshPhongMaterial({ map: this.createTextTexture('AI/ML') }),
            new THREE.MeshPhongMaterial({ map: this.createTextTexture('DevOps') })
        ];
        this.cube = new THREE.Mesh(this.geometry, this.materials);
        scene.add(this.cube);
    }

    createTextTexture(text) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = 256;
        canvas.height = 256;
        
        // Background
        ctx.fillStyle = '#1a1a1a';
        ctx.fillRect(0, 0, 256, 256);
        
        // Text
        ctx.font = '40px Arial';
        ctx.fillStyle = '#FF71CE';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(text, 128, 128);
        
        const texture = new THREE.CanvasTexture(canvas);
        return texture;
    }

    animate() {
        this.cube.rotation.x += 0.01;
        this.cube.rotation.y += 0.01;
    }
}

// Floating particles system
class ParticleSystem {
    constructor() {
        const geometry = new THREE.BufferGeometry();
        const vertices = [];
        const colors = [];

        for (let i = 0; i < 1000; i++) {
            vertices.push(
                Math.random() * 20 - 10,
                Math.random() * 20 - 10,
                Math.random() * 20 - 10
            );

            colors.push(
                Math.random() * 0.5 + 0.5,
                Math.random() * 0.5,
                Math.random() * 0.5 + 0.5
            );
        }

        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

        const material = new THREE.PointsMaterial({
            size: 0.05,
            vertexColors: true,
            transparent: true,
            opacity: 0.8
        });

        this.particles = new THREE.Points(geometry, material);
        scene.add(this.particles);
    }

    animate() {
        this.particles.rotation.y += 0.001;
    }
}

// Initialize components
function init() {
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.getElementById('skills-3d').appendChild(renderer.domElement);

    // Camera position
    camera.position.z = 5;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0xFF71CE, 1);
    pointLight.position.set(5, 5, 5);
    scene.add(pointLight);

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;

    // Create components
    const skillsCube = new SkillsCube();
    const particleSystem = new ParticleSystem();

    // Animation loop
    function animate() {
        requestAnimationFrame(animate);
        skillsCube.animate();
        particleSystem.animate();
        controls.update();
        renderer.render(scene, camera);
    }
    animate();
}

// Handle window resize
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', init);
