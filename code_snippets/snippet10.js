const generateSectionHTML = (section, user) => {
    const sectionData = section.data || {};
    
    console.log(`Processing section: ${section.name}`);
    console.log(`Section data keys:`, Object.keys(sectionData));
    
    switch (section.name) {
      case 'Profile':
        const summary = sectionData.summary || sectionData.bio || (user && user.bio) || 'Professional summary goes here';
        return `
          <div class="section">
            <h2>Professional Summary</h2>
            <div class="description">${summary}</div>
          </div>
        `;
        
      case 'Experience':
        const experiences = sectionData.experiences || sectionData.experience || [];
        console.log(`Experience entries: ${experiences.length}`);
        
        if (!experiences.length) return '';
        
        const experienceHTML = experiences.map(exp => `
          <div class="item">
            <h3>${exp.position || exp.title || 'Job Title'}</h3>
            <div class="company">${exp.company || 'Company Name'}</div>
            <div class="date">${formatDate(exp.startDate)} - ${exp.isCurrent ? 'Present' : formatDate(exp.endDate)}</div>
            <div class="description">${exp.description || 'Job description'}</div>
          </div>
        `).join('');
        
        return `
          <div class="section">
            <h2>Experience</h2>
            ${experienceHTML}
          </div>
        `;
        
      case 'Education':
        const educations = sectionData.educations || sectionData.education || [];
        console.log(`Education entries: ${educations.length}`);
        
        if (!educations.length) return '';
        
        const educationHTML = educations.map(edu => `
          <div class="item">
            <h3>${edu.degree || 'Degree'}</h3>
            <div class="company">${edu.institution || 'Institution'}</div>
            <div class="date">${formatDate(edu.startDate)} - ${edu.isCurrent ? 'Present' : formatDate(edu.endDate)}</div>
            ${edu.gpa ? `<div class="description">GPA: ${edu.gpa}</div>` : ''}
          </div>
        `).join('');
        
        return `
          <div class="section">
            <h2>Education</h2>
            ${educationHTML}
          </div>
        `;
        
      case 'Skills':
        const technical = sectionData.technical || [];
        const soft = sectionData.soft || [];
        const allSkills = [...technical, ...soft];
        console.log(`Skills: technical=${technical.length}, soft=${soft.length}, total=${allSkills.length}`);
        
        if (!allSkills.length) return '';
        
        const skillsHTML = allSkills.map(skill => 
          `<span class="skill">${skill}</span>`
        ).join('');
        
        return `
          <div class="section">
            <h2>Skills</h2>
            <div class="skills">${skillsHTML}</div>
          </div>
        `;
        
      case 'Languages':
        const languages = sectionData.languages || [];
        console.log(`Languages: ${languages.length}`);
        
        if (!languages.length) return '';
        
        const languagesHTML = languages.map(lang => `
          <div class="item">
            <h3>${lang.name || 'Language'}</h3>
            <div class="description">${lang.level || 'Proficient'}</div>
          </div>
        `).join('');
        
        return `
          <div class="section">
            <h2>Languages</h2>
            ${languagesHTML}
          </div>
        `;
        
      case 'Projects':
        const projects = sectionData.projects || [];
        console.log(`Projects: ${projects.length}`);
        
        if (!projects.length) return '';
        
        const projectsHTML = projects.map(project => `
          <div class="item">
            <h3>${project.name || 'Project'}</h3>
            <div class="date">${formatDate(project.startDate)} - ${project.endDate ? formatDate(project.endDate) : 'Ongoing'}</div>
            <div class="description">${project.description || 'Project description'}</div>
          </div>
        `).join('');
        
        return `
          <div class="section">
            <h2>Projects</h2>
            ${projectsHTML}
          </div>
        `;
        
      case 'Publications':
        const publications = sectionData.publications || [];
        console.log(`Publications: ${publications.length}`);
        
        if (!publications.length) return '';
        
        const publicationsHTML = publications.map(pub => {
          const authorsList = pub.authors && Array.isArray(pub.authors) 
            ? pub.authors.map(author => author.name || author).join(', ')
            : 'Authors';
          return `
            <div class="item">
              <h3>${pub.title || 'Publication'}</h3>
              <div class="company">${authorsList}</div>
              <div class="date">${pub.publisher || 'Publisher'} • ${formatDate(pub.publicationDate)}</div>
              ${pub.doi ? `<div class="description">DOI: ${pub.doi}</div>` : ''}
            </div>
          `;
        }).join('');
        
        return `
          <div class="section">
            <h2>Publications</h2>
            ${publicationsHTML}
          </div>
        `;
        
      case 'Awards':
        const awards = sectionData.awards || [];
        console.log(`Awards: ${awards.length}`);
        
        if (!awards.length) return '';
        
        const awardsHTML = awards.map(award => `
          <div class="item">
            <h3>${award.title || 'Award'}</h3>
            <div class="company">${award.issuer || 'Organization'}</div>
            <div class="date">${formatDate(award.dateReceived)}</div>
          </div>
        `).join('');
        
        return `
          <div class="section">
            <h2>Awards</h2>
            ${awardsHTML}
          </div>
        `;
        
      case 'References':
        const references = sectionData.references || [];
        console.log(`References: ${references.length}`);
        
        if (!references.length) return '';
        
        const referencesHTML = references.map(ref => `
          <div class="item">
            <h3>${ref.name || 'Reference'}</h3>
            <div class="company">${ref.position || 'Position'} at ${ref.company || 'Company'}</div>
            <div class="description">${ref.email || 'Email'} | ${ref.phone || 'Phone'}</div>
          </div>
        `).join('');
        
        return `
          <div class="section">
            <h2>References</h2>
            ${referencesHTML}
          </div>
        `;
        
      default:
        console.log(`Unknown section: ${section.name}`);
        return '';
    }
  };