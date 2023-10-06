parent = window.parent.document || window.document;

const findSideBar = () => {
  const sideBar = parent.querySelectorAll('section[data-testid="stSidebar"]');
  console.log(`sideBar: ${sideBar}, body: ${parent.body}`);
  if (sideBar) {
    return sideBar[0];
  }
  return null;
};

// Container for the logo
const docqLogoContainer = document.createElement("div");
docqLogoContainer.setAttribute("class", "docq-logo-container");
docqLogoContainer.setAttribute("id", "docq-logo-container");
docqLogoContainer.setAttribute(
  "style",
  "display: flex; justify-content: center; align-items: center; width: 100%; position: sticky; top: 0; z-index: 1000; background-color: transparent; flex-direction: column; padding: 10px;"
);

// Close button
const closeButton = document.createElement("button");
closeButton.setAttribute("id", "docq-close-button");
closeButton.setAttribute(
  "style",
  "position: absolute; right: 10px; top: 10px; background-color: transparent; border: none; outline: none; cursor: pointer;"
);
closeButton.setAttribute("kind", "header");
closeButton.innerText = "X";

parent.querySelector("button[kind='header']")?.remove();
docqLogoContainer.appendChild(closeButton);

// Logo
const docqLogo = document.createElement("img");
docqLogo.setAttribute(
  "src",
  "https://github.com/docqai/docq/blob/main/docs/assets/logo.jpg?raw=true"
);
docqLogo.setAttribute("alt", "docq logo");
docqLogo.setAttribute("style", "width: 50px; height: 50px;");
docqLogo.setAttribute("id", "docq-logo");
docqLogo.setAttribute("async", "1");

docqLogoContainer.appendChild(docqLogo);

// Selcted org info
const selectedOrgInfo = document.createElement("div");
selectedOrgInfo.setAttribute("id", "docq-selected-org-info");
selectedOrgInfo.setAttribute("style", "margin-top: 10px;");
selectedOrgInfo.innerHTML = `
  <span> Selected org: </span> <br />
  <span style="font-size: 12px;">
    <strong>{{org}}</strong>
  </span>
`;

docqLogoContainer.appendChild(selectedOrgInfo);

// Change org link
const changeOrgButton = document.createElement("a");
changeOrgButton.setAttribute("id", "docq-change-org-button");
changeOrgButton.setAttribute("style", "margin-top: 10px;");
changeOrgButton.setAttribute("href", "http://172.26.68.148:8501/Admin_Orgs");
// changeOrgButton.setAttribute("target", "_blank");
changeOrgButton.innerHTML = "<span>Change org</span>";

docqLogoContainer.appendChild(changeOrgButton);


const sideBar = findSideBar();

// Add close script to parent
const closeScript = document.createElement("script");
closeScript.innerHTML = `
    function docqClose() {
      const sideBar = document.querySelectorAll('section[data-testid="stSidebar"]');
      if (sideBar) {
        console.log('Closing sidebar')
        sideBar[0].setAttribute("aria-expanded", "false");
        sideBar[0].setAttribute("aria-hidden", "true");
        sideBar[0].setAttribute("style", "display: none;");
      }
    }
    `;

parent.body.appendChild(closeScript);

if (sideBar) {
  // Check if the logo already exists
  const docqLogo = parent.getElementById("docq-logo-container");
  if (docqLogo) {
    docqLogo.remove();
  }
  sideBar.insertBefore(docqLogoContainer, sideBar.firstChild);
}
