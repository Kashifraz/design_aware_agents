const renderSection = (title, content) => `
  <div class="section">
    <h2>${title}</h2>
    ${content}
  </div>
`;

const renderItems = (items, itemRenderer) => items.map(itemRenderer).join('');

const renderProfileSection = (sectionData, user) => {
  const summary =
    sectionData.summary ||
    sectionData.bio ||
    (user && user.bio) ||
    'Professional summary goes here';

  return renderSection(
    'Professional Summary',
    `<div class="description">${summary}</div>`
  );
};

const renderExperienceSection = sectionData => {
  const experiences = sectionData.experiences || sectionData.experience || [];
  console.log(`Experience entries: ${experiences.length}`);

  if (!experiences.length) return '';

  const experienceHTML = renderItems(experiences, exp => `
    <div class="item">
      <h3>${exp.position || exp.title || 'Job Title'}</h3>
      <div class="company">${exp.company || 'Company Name'}</div>
      <div class="date">${formatDate(exp.startDate)} - ${exp.isCurrent ? 'Present' : formatDate(exp.endDate)}</div>
      <div class="description">${exp.description || 'Job description'}</div>
    </div>
  `);

  return renderSection('Experience', experienceHTML);
};

const renderEducationSection = sectionData => {
  const educations = sectionData.educations || sectionData.education || [];
  console.log(`Education entries: ${educations.length}`);

  if (!educations.length) return '';

  const educationHTML = renderItems(educations, edu => `
    <div class="item">
      <h3>${edu.degree || 'Degree'}</h3>
      <div class="company">${edu.institution || 'Institution'}</div>
      <div class="date">${formatDate(edu.startDate)} - ${edu.isCurrent ? 'Present' : formatDate(edu.endDate)}</div>
      ${edu.gpa ? `<div class="description">GPA: ${edu.gpa}</div>` : ''}
    </div>
  `);

  return renderSection('Education', educationHTML);
};

const renderSkillsSection = sectionData => {
  const technical = sectionData.technical || [];
  const soft = sectionData.soft || [];
  const allSkills = [...technical, ...soft];
  console.log(`Skills: technical=${technical.length}, soft=${soft.length}, total=${allSkills.length}`);

  if (!allSkills.length) return '';

  const skillsHTML = allSkills.map(skill => `<span class="skill">${skill}</span>`).join('');

  return renderSection(
    'Skills',
    `<div class="skills">${skillsHTML}</div>`
  );
};

const renderLanguagesSection = sectionData => {
  const languages = sectionData.languages || [];
  console.log(`Languages: ${languages.length}`);

  if (!languages.length) return '';

  const languagesHTML = renderItems(languages, lang => `
    <div class="item">
      <h3>${lang.name || 'Language'}</h3>
      <div class="description">${lang.level || 'Proficient'}</div>
    </div>
  `);

  return renderSection('Languages', languagesHTML);
};

const renderProjectsSection = sectionData => {
  const projects = sectionData.projects || [];
  console.log(`Projects: ${projects.length}`);

  if (!projects.length) return '';

  const projectsHTML = renderItems(projects, project => `
    <div class="item">
      <h3>${project.name || 'Project'}</h3>
      <div class="date">${formatDate(project.startDate)} - ${project.endDate ? formatDate(project.endDate) : 'Ongoing'}</div>
      <div class="description">${project.description || 'Project description'}</div>
    </div>
  `);

  return renderSection('Projects', projectsHTML);
};

const renderPublicationsSection = sectionData => {
  const publications = sectionData.publications || [];
  console.log(`Publications: ${publications.length}`);

  if (!publications.length) return '';

  const publicationsHTML = renderItems(publications, pub => {
    const authorsList =
      pub.authors && Array.isArray(pub.authors)
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
  });

  return renderSection('Publications', publicationsHTML);
};

const renderAwardsSection = sectionData => {
  const awards = sectionData.awards || [];
  console.log(`Awards: ${awards.length}`);

  if (!awards.length) return '';

  const awardsHTML = renderItems(awards, award => `
    <div class="item">
      <h3>${award.title || 'Award'}</h3>
      <div class="company">${award.issuer || 'Organization'}</div>
      <div class="date">${formatDate(award.dateReceived)}</div>
    </div>
  `);

  return renderSection('Awards', awardsHTML);
};

const renderReferencesSection = sectionData => {
  const references = sectionData.references || [];
  console.log(`References: ${references.length}`);

  if (!references.length) return '';

  const referencesHTML = renderItems(references, ref => `
    <div class="item">
      <h3>${ref.name || 'Reference'}</h3>
      <div class="company">${ref.position || 'Position'} at ${ref.company || 'Company'}</div>
      <div class="description">${ref.email || 'Email'} | ${ref.phone || 'Phone'}</div>
    </div>
  `);

  return renderSection('References', referencesHTML);
};

const sectionRenderers = {
  Profile: renderProfileSection,
  Experience: renderExperienceSection,
  Education: renderEducationSection,
  Skills: renderSkillsSection,
  Languages: renderLanguagesSection,
  Projects: renderProjectsSection,
  Publications: renderPublicationsSection,
  Awards: renderAwardsSection,
  References: renderReferencesSection
};

const generateSectionHTML = (section, user) => {
  const sectionData = section.data || {};

  console.log(`Processing section: ${section.name}`);
  console.log(`Section data keys:`, Object.keys(sectionData));

  const renderer = sectionRenderers[section.name];

  if (!renderer) {
    console.log(`Unknown section: ${section.name}`);
    return '';
  }

  return renderer(sectionData, user);
};