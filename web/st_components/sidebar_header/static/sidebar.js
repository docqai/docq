// SIDEBAR-HEADER-SCRIPT === DO NOT REMOVE THIS COMMENT --- Used to identify this script in the page header
const __parent = window.parent.document || window.document;

// === Required params ===
const selectedOrg = `{{selected_org}}`;
const orgOptionsJson = `{{org_options_json}}`;
const styleDoc = `{{style_doc}}`;
const orgSelectorLabel = `{{org_selector_label}}`;
const authState = `{{auth_state}}`;

// === Optional params ===
const logoUrl = `{{logo_url}}`;


const matchParamNotSet = /\{\{.*\}\}/g;


// === Style document ======================================================================================================================================================
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

// === Util functions ======================================================================================================================================================
const findSideBar = () => {
  const sideBar = __parent.querySelectorAll('section[data-testid="stSidebar"]');
  if (sideBar) {
    return sideBar[0];
  }
  return null;
};

/**
 * Create dropdown option
 * @param {string} value dropdown option value 
 * @param {string} text dropdown option text 
 * @returns {HTMLOptionElement} HTML option element
 */
function createSelectOption (value, text) {
  const option = document.createElement("option");
  option.setAttribute("value", value);
  option.setAttribute("class", "docq-select-option")
  option.innerHTML = text;
  return option;
}

// === End util functions ==============================


// === Container for the logo =============================================================================================================================================
const docqLogoContainer = document.createElement("div");
docqLogoContainer.setAttribute("class", "docq-logo-container");
docqLogoContainer.setAttribute("id", "docq-logo-container");
docqLogoContainer.setAttribute(
  "style",
  "display: flex; justify-content: center; align-items: center; width: 100%; position: sticky; top: 0; z-index: 1000; background-color: transparent; flex-direction: column; padding: 10px;"
);

// === Close button ==========================================================
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

// === Logo =================================================================================================
const docqLogo = document.createElement("img");

const logoSrc = logoUrl && !logoUrl.match(matchParamNotSet) ? logoUrl : "https://github.com/docqai/docq/blob/main/docs/assets/logo.jpg?raw=true"

docqLogo.setAttribute("src", logoSrc);
docqLogo.setAttribute("alt", "docq logo");
docqLogo.setAttribute("style", "width: 25%;");
docqLogo.setAttribute("id", "docq-logo");
docqLogo.setAttribute("async", "1");

docqLogoContainer.appendChild(docqLogo);


// === Dropdown menu ==========================================================================================

const orgDropdown = document.createElement("div");
orgDropdown.setAttribute("id", "docq-org-dropdown");
orgDropdown.setAttribute("style", "margin-top: 10px;");

const selectLabel = document.createElement("label");
selectLabel.setAttribute("for", "docq-org-dropdown-select");
selectLabel.setAttribute("class", "docq-select-label");
selectLabel.innerHTML = "Select org:";
if (!matchParamNotSet.test(orgSelectorLabel)) {
  selectLabel.innerHTML = orgSelectorLabel;
}

selectLabel.setAttribute("style", "margin-right: 10px;");

const selectMenu = document.createElement("select");
selectMenu.setAttribute("id", "docq-org-dropdown-select");
selectMenu.setAttribute("onchange", "selectOrg(this.value)");

if (orgOptionsJson && !orgOptionsJson.match(matchParamNotSet)) {
  const orgOptions = JSON.parse(orgOptionsJson);
  orgOptions.forEach((org) => {
    const option = createSelectOption(org, org);
    if (org === selectedOrg) {
      option.setAttribute("selected", "selected");
    }
    selectMenu.appendChild(option);
  });
};

orgDropdown.appendChild(selectLabel);
orgDropdown.appendChild(selectMenu);

if (!selectedOrg.match(matchParamNotSet) && !orgOptionsJson.match(matchParamNotSet) && authState === "authenticated") {
  docqLogoContainer.appendChild(orgDropdown);
}


const sideBar = findSideBar();


if (sideBar) {
  // Check if the logo already exists
  const docqLogo = __parent.getElementById("docq-logo-container");
  if (docqLogo) {
    docqLogo.remove();
  }
  sideBar.insertBefore(docqLogoContainer, sideBar.firstChild);
}


// === Add scripts to parent document ===
const selectOrgScript = document.createElement("script");
selectOrgScript.setAttribute("type", "text/javascript");
selectOrgScript.setAttribute("id", "docq-select-org-script");
selectOrgScript.innerHTML = `
  function selectOrg(org) {
    const timeStamp = new Date().getTime();
    const orgParam = encodeURIComponent(btoa(org + "::" + timeStamp));
    window.parent.location.href = \`?org=\${orgParam}\`;
  }
`;

const prevScript =__parent.getElementById("docq-select-org-script");
if (prevScript) {
  prevScript.remove();
}

__parent.body.appendChild(selectOrgScript);

// ===
const iframes =__parent.querySelectorAll("iframe");
iframes.forEach((iframe) => {
  const srcdoc = iframe.getAttribute("srcdoc");
  if (srcdoc.includes("SIDEBAR-HEADER-SCRIPT")) {
    iframe.parentNode.setAttribute("class", "docq-iframe-container");
  }
});
// === EOF =================================================================================================================================================================
