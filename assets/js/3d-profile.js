// Import Three.js from CDN
import * as THREE from 'https://cdn.skypack.dev/three@0.136.0';

// Initialize scene
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ alpha: true });

// Skills Sphere
class SkillsSphere {
    constructor() {
        this.geometry = new THREE.SphereGeometry(2, 32, 32);
        this.material = new THREE.ShaderMaterial({
            uniforms: {
                time: { value: 0 },
                resolution: { value: new THREE.Vector2() }
            },
            vertexShader: `
                varying vec2 vUv;
                varying vec3 vPosition;
                void main() {
                    vUv = uv;
                    vPosition = position;
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                }
            `,
            fragmentShader: `
                uniform float time;
                varying vec2 vUv;
                varying vec3 vPosition;
                
                void main() {
                    vec3 color1 = vec3(1.0, 0.0, 0.6); // Hot pink
                    vec3 color2 = vec3(0.0, 1.0, 0.6); // Neon green
                    
                    float pattern = sin(vPosition.x * 10.0 + time) * 
                                  sin(vPosition.y * 10.0 + time) * 
                                  sin(vPosition.z * 10.0 + time);
                    
                    vec3 finalColor = mix(color1, color2, pattern);
                    gl_FragColor = vec4(finalColor, 1.0);
                }
            `
        });
        this.sphere = new THREE.Mesh(this.geometry, this.material);
        scene.add(this.sphere);
    }

    animate(time) {
        this.material.uniforms.time.value = time;
        this.sphere.rotation.x += 0.01;
        this.sphere.rotation.y += 0.01;
    }
}

// Floating Text
class FloatingText {
    constructor(text, position) {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = 256;
        canvas.height = 256;

        // Draw text
        context.fillStyle = '#00ff99';
        context.font = '32px Arial';
        context.fillText(text, 10, 128);

        const texture = new THREE.CanvasTexture(canvas);
        const material = new THREE.SpriteMaterial({ map: texture });
        this.sprite = new THREE.Sprite(material);
        this.sprite.position.set(...position);
        scene.add(this.sprite);
    }

    animate() {
        this.sprite.position.y += Math.sin(Date.now() * 0.001) * 0.01;
    }
}

// Initialize components
function init() {
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.getElementById('skills-3d').appendChild(renderer.domElement);

    camera.position.z = 5;

    // Create components
    const skillsSphere = new SkillsSphere();
    const skills = [
        'Python', 'React', 'Node.js', 'AI/ML',
        'MongoDB', 'AWS', 'Docker', 'TensorFlow'
    ];

    const floatingTexts = skills.map((skill, i) => {
        const angle = (i / skills.length) * Math.PI * 2;
        const x = Math.cos(angle) * 3;
        const y = Math.sin(angle) * 3;
        return new FloatingText(skill, [x, y, 0]);
    });

    // Animation loop
    function animate() {
        requestAnimationFrame(animate);
        skillsSphere.animate(Date.now() * 0.001);
        floatingTexts.forEach(text => text.animate());
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
