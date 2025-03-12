import * as THREE from 'three';
import { TextGeometry } from 'three/addons/geometries/TextGeometry.js';
import { FontLoader } from 'three/addons/loaders/FontLoader.js';

// Scene setup
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.getElementById('skills-3d').appendChild(renderer.domElement);

// Lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambientLight);
const pointLight = new THREE.PointLight(0xffffff, 1);
pointLight.position.set(5, 5, 5);
scene.add(pointLight);

// Skills array
const skills = [
    { text: "Python", color: 0x3776AB },
    { text: "React", color: 0x61DAFB },
    { text: "Node.js", color: 0x339933 },
    { text: "MongoDB", color: 0x47A248 },
    { text: "TensorFlow", color: 0xFF6F00 }
];

// Create floating skills
const loader = new FontLoader();
loader.load('https://threejs.org/examples/fonts/helvetiker_regular.typeface.json', function(font) {
    skills.forEach((skill, index) => {
        const geometry = new TextGeometry(skill.text, {
            font: font,
            size: 0.5,
            height: 0.2,
        });
        const material = new THREE.MeshPhongMaterial({ color: skill.color });
        const mesh = new THREE.Mesh(geometry, material);
        
        // Position in a circle
        const angle = (index / skills.length) * Math.PI * 2;
        mesh.position.x = Math.cos(angle) * 3;
        mesh.position.z = Math.sin(angle) * 3;
        mesh.position.y = Math.sin(Date.now() * 0.001 + index) * 0.5;
        
        scene.add(mesh);
    });
});

// Animation
camera.position.z = 5;
function animate() {
    requestAnimationFrame(animate);
    
    // Rotate camera around scene
    const time = Date.now() * 0.001;
    camera.position.x = Math.cos(time * 0.5) * 5;
    camera.position.z = Math.sin(time * 0.5) * 5;
    camera.lookAt(scene.position);
    
    // Update skill positions
    scene.children.forEach((child, index) => {
        if (child instanceof THREE.Mesh) {
            child.position.y = Math.sin(time + index) * 0.5;
            child.rotation.y = time * 0.3;
        }
    });
    
    renderer.render(scene, camera);
}
animate();
