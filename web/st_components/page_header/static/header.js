// PAGE-HEADER-SCRIPT === DO NOT REMOVE THIS COMMENT --- Used to identify this script in the page header
const __parent = window.parent.document || window.document;

// Get params === These are to be set in the template by the method that loads this script
const username = `{{username}}`; // User name to be displayed in the header
const selectedOrg = `{{selected_org}}`; // Selected org name
const avatarSrc = `{{avatar_src}}`; // Avatar image source
const styleDoc = `{{style_doc}}`; // CSS string to be added to the __parent.document.head
const authState = `{{auth_state}}`; // "authenticated" or "unauthenticated"

const matchParamNotSet = /\{\{.*\}\}/;



// Add style to the parent document head
if (!matchParamNotSet.test(styleDoc)) {
  const style = __parent.createElement("style");
  style.setAttribute("id", "docq-header-style");
  // check if style tag already exists and verify if it is the same as the one to be added
  const prevStyle = __parent.getElementById("docq-header-style");
  if (prevStyle && prevStyle.innerHTML !== styleDoc) {
    prevStyle.innerHTML = styleDoc;
  } else {
    style.innerHTML = styleDoc;
    __parent.head.appendChild(style);
  }  
}

// === Utility functions // ===

/**
 * Creates a horizontal divider for the user menu
 * @returns {HTMLDivElement} The horizontal divider
 */
function createHorizontalDivider(){
  const divider = __parent.createElement('div')
  divider.setAttribute('class', 'docq-user-menu-divider')
  return divider
}

// End utility functions ==============

// Container
const docqContainer = document.createElement("div");
docqContainer.setAttribute("id", "docq-header-container");


// Create header divs
const [left, center, right] = ["left", "center", "right"].map((id) => {
  const div = document.createElement("div");
  div.setAttribute("id", `docq-header-${id}`);
  div.setAttribute("class", `docq-header header-${id}`);
  return div;
});


// Avatar
const loadAvatar = () => {
  const avatar = document.createElement("img");
  const src = matchParamNotSet.test(avatarSrc) ? "https://www.gravatar.com/avatar/00" : avatarSrc;
  avatar.setAttribute("src", src);
  avatar.setAttribute("alt", "user-avatar");
  avatar.setAttribute("style", "width: 20px; height: 20px;");
  avatar.setAttribute("id", "docq-img-avatar");
  avatar.setAttribute("async", "1");
  return avatar;
}

// Avatar container
const avatarContainer = document.createElement("div");
avatarContainer.setAttribute("id", "docq-avatar-container");


const avatar = loadAvatar();

// user menu
const userMenu = document.createElement("div");
userMenu.setAttribute("id", "docq-user-menu");
userMenu.setAttribute("class", "docq-user-menu");

// Open user menu on click
avatar.addEventListener("click", (e) => {
  e.preventDefault();
  userMenu.classList.toggle("docq-user-menu-active");
});

// Close user menu on click outside
__parent.addEventListener("click", (e) => {
  if (!avatarContainer.contains(e.target)) {
    userMenu.classList.remove("docq-user-menu-active");
  }
});

// Create a profile and add it to the user menu
const profile = document.createElement("div");
profile.setAttribute("class", "docq-user-menu-profile");
profile.innerHTML = `
  <div class="docq-user-menu-profile-avatar">
    ${avatar.outerHTML}
  </div>
  <div class="docq-user-menu-profile-name">
    <span>${username}</span>
  </div>
`;

userMenu.appendChild(profile);
userMenu.appendChild(createHorizontalDivider());

avatarContainer.appendChild(userMenu);

// End user menu

if (authState === "authenticated" && !matchParamNotSet.test(avatarSrc)) {
  avatarContainer.appendChild(avatar);
}


/* User name */
const userName = document.createElement("span");
userName.innerHTML = `<strong>${username}@${selectedOrg}</strong>`;
userName.setAttribute("id", "docq-user-name");

if(!matchParamNotSet.test(username) && authState === "authenticated") {
  left.appendChild(userName);
}
if (!matchParamNotSet.test(avatarSrc) && authState === "authenticated") {
  left.appendChild(avatarContainer);
}


// Page title
const pageTitle = document.createElement("span");



// Insert docq left, center, right divs
[right, center, left].forEach((div) => docqContainer.appendChild(div));


// Insert docq container in the DOM
stApp = __parent.querySelector("header[data-testid='stHeader']");
if (stApp) {
  const prevDocqContainer = __parent.getElementById("docq-header-container");
  if (prevDocqContainer) {
    prevDocqContainer.remove();
  }
  stApp.insertBefore(docqContainer, stApp.firstChild);
}


// ===
const iframes = __parent.querySelectorAll("iframe");
iframes.forEach((iframe) => {
  const srcdoc = iframe.getAttribute("srcdoc");
  if (srcdoc.includes("PAGE-HEADER-SCRIPT")) {
    iframe.parentNode.setAttribute("class", "docq-iframe-container");
  }
});
