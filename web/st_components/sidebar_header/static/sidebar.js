// SIDEBAR-HEADER-SCRIPT === DO NOT REMOVE THIS COMMENT --- Used to identify this script in the page header
const __parent = window.parent.document || window.document;

// === Required params ===
const styleDoc = `{{style_doc}}`;

// === Optional params ===
const logoUrl = `{{logo_url}}`;


const matchParamNotSet = /\{\{.*\}\}/g;


// === Style document =======================================
const styleDocElement = document.createElement("style");
styleDocElement.setAttribute("id", "docq-sidebar-style-doc");

if (!matchParamNotSet.test(styleDoc)) {
  styleDocElement.innerHTML = styleDoc;
  const prevStyleDoc = __parent.getElementById("docq-sidebar-style-doc");
  if (prevStyleDoc && prevStyleDoc.innerHTML !== styleDoc) {
    prevStyleDoc.innerHTML = styleDoc;
  } else {
    __parent.head.appendChild(styleDocElement);
  }
}

// === Util functions ================================
const findSideBar = () => {
  const sideBar = __parent.querySelectorAll('section[data-testid="stSidebar"]');
  if (sideBar) {
    return sideBar[0];
  }
  return null;
};
// === End util functions ===


// === Container for the logo ========================
const docqLogoContainer = document.createElement("div");
docqLogoContainer.setAttribute("class", "docq-logo-container");
docqLogoContainer.setAttribute("id", "docq-logo-container");
docqLogoContainer.setAttribute(
  "style",
  "display: flex; justify-content: center; align-items: center; width: 100%; position: sticky; top: 0; z-index: 1000; background-color: transparent; flex-direction: column; padding: 10px;"
);

// === Close button ==================================
const closeIcon = `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="currentColor" xmlns="http://www.w3.org/2000/svg" color="inherit" class="e1ugi8lo1 css-fblp2m ex0cdmw0"><path fill="none" d="M0 0h24v24H0V0z"></path><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"></path></svg>`;
const closeButton = document.createElement("button");
closeButton.setAttribute("id", "docq-close-button");
closeButton.setAttribute(
  "style",
  "position: absolute; right: 10px; top: 10px; background-color: transparent; border: none; outline: none; cursor: pointer;"
);
closeButton.innerHTML = closeIcon;

// Close sidebar on click
closeButton.addEventListener("click", () => {
  const closeBtn = __parent.querySelector(
    'section[data-testid="stSidebar"][aria-expanded="true"] button[kind="header"]'
  );
  if (closeBtn) {
    closeBtn.click();
  } else {
    console.log("Close button not found", closeBtn);
  }
});

docqLogoContainer.appendChild(closeButton);

// === Logo ================================================
const docqLogo = document.createElement("img");

const logoSrc = logoUrl && !logoUrl.match(matchParamNotSet) ? logoUrl : "https://github.com/docqai/docq/blob/main/docs/assets/logo.jpg?raw=true"

const docqLogoLink = document.createElement("a");
docqLogoLink.setAttribute("href", "/");
docqLogoLink.setAttribute("target", "_self");
docqLogoLink.setAttribute("style", "text-decoration: none; width: 25% !important;");
docqLogoLink.setAttribute("id", "docq-logo-link");

docqLogo.setAttribute("src", logoSrc);
docqLogo.setAttribute("alt", "docq logo");
docqLogo.setAttribute("style", "width: 100%;");
docqLogo.setAttribute("id", "docq-logo");
docqLogo.setAttribute("async", "1");

docqLogoLink.appendChild(docqLogo);

docqLogoContainer.appendChild(docqLogoLink);

const sideBar = findSideBar();


if (sideBar) {
  // Check if the logo already exists
  const docqLogo = __parent.getElementById("docq-logo-container");
  if (!docqLogo || docqLogo.innerHTML !== docqLogoContainer.innerHTML) {
    if(docqLogo) docqLogo.remove();
    sideBar.insertBefore(docqLogoContainer, sideBar.firstChild);
  }
}

const iframes =__parent.querySelectorAll("iframe");
iframes.forEach((iframe) => {
  const srcdoc = iframe.getAttribute("srcdoc");
  if (srcdoc.includes("SIDEBAR-HEADER-SCRIPT")) {
    iframe.parentNode.setAttribute("class", "docq-iframe-container");
  }
});
// === EOF ===
