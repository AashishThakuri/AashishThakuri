<!-- Custom CSS for 3D effects -->
<link rel="stylesheet" href="assets/css/profile-3d.css">

<!-- Custom 3D Header -->
<div align="center">
  <div class="profile-3d-container">
    <div class="card-3d">
      <div class="card-front">
        <img src="https://avatars.githubusercontent.com/u/AashishThakuri" width="150" style="border-radius: 50%; border: 3px solid #FF71CE; box-shadow: 0 0 20px #FF71CE;">
        <h1 style="color: #FF71CE; text-shadow: 0 0 10px #FF71CE;">Aashish Thakuri</h1>
        <p style="color: #fff;">Creative Developer & AI Enthusiast</p>
      </div>
      <div class="card-back">
        <h2 style="color: #FF71CE;">About Me</h2>
        <p style="color: #fff; text-align: center;">
          🎓 Student at Kathmandu University<br>
          💻 Full Stack Developer<br>
          🤖 AI/ML Enthusiast<br>
          🚀 Founder of Advance Data Science Classroom
        </p>
      </div>
    </div>
  </div>
</div>

<!-- Interactive 3D Skills Display -->
<div id="skills-3d" style="width: 100%; height: 400px; margin: 20px 0;">
  <!-- Three.js will render here -->
</div>
<script type="module" src="assets/js/profile-3d.js"></script>

<!-- Dynamic Code Section -->
```typescript
interface Developer {
  name: string;
  title: string;
  location: string;
  skills: Skills;
  projects: Project[];
  contact: Contact;
}

interface Skills {
  languages: string[];
  frameworks: string[];
  databases: string[];
  ai_ml: string[];
  tools: string[];
}

interface Project {
  name: string;
  description: string;
  tech_stack: string[];
  impact: string;
}

interface Contact {
  email: string;
  linkedin: string;
  twitter: string;
  portfolio: string;
}

const aashish: Developer = {
  name: "Aashish Thakuri",
  title: "Creative Developer & AI Enthusiast",
  location: "Kathmandu University, Nepal 🇳🇵",
  
  skills: {
    languages: ["Python", "TypeScript", "JavaScript", "Java"],
    frameworks: ["React", "Next.js", "Node.js", "Express"],
    databases: ["MongoDB", "PostgreSQL", "Firebase"],
    ai_ml: ["TensorFlow", "PyTorch", "Scikit-learn"],
    tools: ["Git", "Docker", "AWS", "Vercel"]
  },
  
  projects: [{
    name: "Advance Data Science Classroom",
    description: "Platform democratizing data science education",
    tech_stack: ["Python", "TensorFlow", "React", "Node.js"],
    impact: "Empowering students with data science skills"
  }],
  
  contact: {
    email: "taashish848@gmail.com",
    linkedin: "aashish-bam-435505351",
    twitter: "Lyrical62785503",
    portfolio: "aashishh.vercel.app"
  }
};

// Life Philosophy
function lifeMotto(): string {
  return `
    while (alive) {
      learn();
      create();
      inspire();
      repeat();
    }
  `;
}
```

<!-- Interactive Stats Section -->
<div align="center">
  <div style="background: linear-gradient(45deg, #FF71CE, #B17ACC); padding: 3px; border-radius: 10px; margin: 20px 0;">
    <div style="background: #0D1117; padding: 20px; border-radius: 8px;">
      <img width="49%" src="https://github-readme-stats.vercel.app/api?username=AashishThakuri&show_icons=true&theme=radical&hide_border=true&bg_color=0D1117&title_color=FF71CE&icon_color=FF71CE&text_color=FFFFFF" />
      <img width="49%" src="https://github-readme-streak-stats.herokuapp.com/?user=AashishThakuri&theme=radical&hide_border=true&background=0D1117&ring=FF71CE&fire=FF71CE&currStreakLabel=FF71CE" />
    </div>
  </div>
  
  <!-- Animated Contribution Graph -->
  <div class="contribution-calendar">
    <img width="100%" src="https://github-readme-activity-graph.vercel.app/graph?username=AashishThakuri&custom_title=Contribution%20Graph&bg_color=0D1117&color=FF71CE&line=FF71CE&point=FFFFFF&area=true&hide_border=true" />
  </div>
</div>

<!-- Featured Projects -->
<div align="center">
  <h2 style="color: #FF71CE; text-shadow: 0 0 10px #FF71CE;">🚀 Featured Projects</h2>
  <div style="display: flex; justify-content: center; gap: 10px;">
    <a href="https://github.com/AashishThakuri/advance-data-science">
      <img src="https://github-readme-stats.vercel.app/api/pin/?username=AashishThakuri&repo=advance-data-science&theme=radical&hide_border=true&bg_color=0D1117&title_color=FF71CE&icon_color=FF71CE" />
    </a>
  </div>
</div>

<!-- Connect Section -->
<div align="center">
  <h2 style="color: #FF71CE; text-shadow: 0 0 10px #FF71CE;">🤝 Let's Connect!</h2>
  <div style="display: flex; justify-content: center; gap: 10px;">
    <a href="mailto:taashish848@gmail.com">
      <img src="https://img.shields.io/badge/Gmail-FF71CE?style=for-the-badge&logo=gmail&logoColor=white" />
    </a>
    <a href="https://www.linkedin.com/in/aashish-bam-435505351/">
      <img src="https://img.shields.io/badge/LinkedIn-FF71CE?style=for-the-badge&logo=linkedin&logoColor=white" />
    </a>
    <a href="https://x.com/Lyrical62785503">
      <img src="https://img.shields.io/badge/Twitter-FF71CE?style=for-the-badge&logo=twitter&logoColor=white" />
    </a>
    <a href="https://aashishh.vercel.app/">
      <img src="https://img.shields.io/badge/Portfolio-FF71CE?style=for-the-badge&logo=About.me&logoColor=white" />
    </a>
  </div>
</div>

<!-- Profile Views Counter -->
<div align="center">
  <br/>
  <img src="https://komarev.com/ghpvc/?username=AashishThakuri&color=FF71CE&style=for-the-badge" />
</div>

<!-- Footer Wave -->
<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=FF71CE&height=100&section=footer" />
