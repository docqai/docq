// PAGE-HEADER-SCRIPT === DO NOT REMOVE THIS COMMENT --- Used to identify this script in the page header
const __parent = window.parent.document || window.document;

// Get params === These are to be set in the template by the method that loads this script
const username = `{{username}}`; // User name to be displayed in the header
const avatarSrc = `{{avatar_src}}`; // Avatar image source
const menuItemsJson = `{{menu_items_json}}`; // [{ "text": "Menu item text", "key": "menu-item-button-key", "icon": "menu-item-icon-html"}]
const styleDoc = `{{style_doc}}`; // CSS string to be added to the __parent.document.head
const fab_config = `{{fab_config}}`; // { "icon": "fab-icon", "label": "tool-tip-text", "key": "fab-button-key" }
const authState = `{{auth_state}}`; // "authenticated" or "unauthenticated"

const matchParamNotSet = /\{\{.*\}\}/;

// Add font awesome icons
const _link = document.createElement('link')
_link.setAttribute('rel', 'stylesheet')
_link.setAttribute('id', 'docq-fa-icon-link')
_link.setAttribute('href', 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css')
const prevIconLink = __parent.getElementById('docq-fa-icon-link')
if (!prevIconLink) {
  __parent.head.appendChild(_link)
}



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

const iconsMap = { "logout": "sign-out", "help": "question-circle",
  "feedback": "commenting-o", "settings": "cog", "profile": "user-circle-o",
  "new chat": "commenting-o", "new ticket": "ticket", "new task": "tasks",
}

/** Utility functions */// ==========================================================================================================================================================

function createFAIcon(name) {
  if (name in iconsMap) {
    name = iconsMap[name]
  }
  return `<i class="fa fa-${name}"></i>` 
}

/**
 * Creates a user menu item using the given text and icon html string 
 * @param {string} text The text to be displayed in the menu item
 * @param {string} name 
 * @returns {HTMLButtonElement} The user menu item
 */
function createUserMenuItem(text, name = null){
  const item = __parent.createElement('button')
  item.setAttribute('class', 'docq-user-menu-item')
  item.setAttribute('id', `docq-user-menu-item-${text.replace(' ', '-')}`)
  if (name) {
    item.innerHTML = `<span>${createFAIcon(name)} ${text}</span>`
  } else {
    item.innerHTML = `<span>${text}</span>`
  }
  return item
}

/**
 * Creates a horizontal divider for the user menu
 * @returns {HTMLDivElement} The horizontal divider
 */
function createHorizontalDivider(){
  const divider = __parent.createElement('div')
  divider.setAttribute('class', 'docq-user-menu-divider')
  return divider
}

// End utility functions ==============================================================================================================================================================

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

if (authState === "authenticated" && !matchParamNotSet.test(avatarSrc)) {
  avatarContainer.appendChild(avatar);
}

// User menu ========================================================================================================================================================================
const userMenu = document.createElement("div");
userMenu.setAttribute("id", "docq-user-menu");
userMenu.setAttribute("class", "docq-user-menu");

// Usermenu items ==========================================================================

// Profile =================================================================================
const userProfile = document.createElement("div");
userProfile.setAttribute("id", "docq-user-menu-profile");
userProfile.setAttribute("class", "docq-user-menu-profile");
userProfile.innerHTML = `<div class="docq-user-profile-avatar">${avatar.outerHTML}</div><div class="docq-user-profile-name">${username}</div>`;

// Logout ===================================================================================
const logoutBtn = createUserMenuItem("Logout", 'logout')
logoutBtn.addEventListener("click", () => {
  const btns = __parent.querySelectorAll('button[kind="primary"]');
  const logoutBtn = Array.from(btns).find((btn) => btn.innerText === "Logout");
  if (logoutBtn) {
    logoutBtn.click();
  } else {
    console.log("Logout button not found", logoutBtn);
  }
})

/** Help and Feedback section */
// Help =====================================================================================
const helpBtn = createUserMenuItem("Help", 'help')
helpBtn.addEventListener("click", () => {
  window.open("https://docq.ai", "_blank");
});

// Send feedback ===========================================================================
const feedbackBtn = createUserMenuItem("Send feedback", 'feedback')
feedbackBtn.addEventListener("click", () => {
  window.open("https://docq.ai", "_blank");
});

// Add items to user menu 
userMenu.appendChild(userProfile);
userMenu.appendChild(createHorizontalDivider())
userMenu.appendChild(logoutBtn)
// Add menu items from json
if (!matchParamNotSet.test(menuItemsJson)) {
  const menuItems = JSON.parse(menuItemsJson)
  menuItems.forEach(item => {
    const icon = item.icon || "square" // default icon
    const menuItem = createUserMenuItem(item.text, icon)
    menuItem.addEventListener('click', () => {
      const btns = __parent.querySelectorAll('button[kind="primary"]');
      const menuItemBtn = Array.from(btns).find((btn) => btn.innerText === item.key);
      if (menuItemBtn) {
        menuItemBtn.click();
      } else {
        console.log(`Menu item button with key ${item.key} not found`, menuItemBtn);
      }
    })
    userMenu.appendChild(menuItem)
  })
}

userMenu.appendChild(createHorizontalDivider())
userMenu.appendChild(helpBtn);
userMenu.appendChild(feedbackBtn);

// Add user menu to avatar container
if (authState === "authenticated") {
  avatarContainer.appendChild(userMenu);
}

// User menu toggle
avatar.addEventListener("click", () => {
  const userMenu = __parent.getElementById("docq-user-menu");
  if (userMenu) {
    userMenu.classList.toggle("docq-user-menu-active");
    // Autofocus on the user menu
    const userMenuItems = userMenu.querySelectorAll(".docq-user-menu-item");
    if (userMenuItems.length > 0) {
      userMenuItems[0].focus();
    }

    // Close user menu on click outside
    const closeUserMenu = (e) => {
      if (!userMenu.contains(__parent.activeElement)) {
        userMenu.classList.remove("docq-user-menu-active");
        __parent.removeEventListener("click", closeUserMenu);
      }
    };
    __parent.addEventListener("click", closeUserMenu);
  } else {
    console.log("User menu not found", userMenu);
  }
});

// User menu animation
const userMenuObserver = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.attributeName === "class") {
      const userMenu = __parent.getElementById("docq-user-menu");
      if (userMenu) {
        if (userMenu.classList.contains("docq-user-menu-active")) {
          userMenu.style.animation = "docq-user-menu-slide-in 0.2s ease-in-out";
        } else {
          userMenu.style.animation = "docq-user-menu-slide-out 0.2s ease-in-out";
        }
      }
    }
  });
});

userMenuObserver.observe(userMenu, { attributes: true });

// Close user menu on clicking its child elements
userMenu.addEventListener("click", (e) => {
  if (e.target !== userMenu) {
    const userMenu = __parent.getElementById("docq-user-menu");
    if (userMenu) {
      userMenu.classList.remove("docq-user-menu-active");
    }
  }
});

// End user menu ====================================================================================================================================================================


/* User name */
const userName = document.createElement("span");
userName.innerHTML = `<strong>${username}</strong>`;
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


// === Floating action button ====================================================================================================================================================
const fabContainer = document.createElement("div");
fabContainer.setAttribute("id", "docq-floating-action-button-container");
fabContainer.setAttribute("class", "docq-floating-action-button-container");

// New chat button
function fabSetup (key, icon) {
  const newChatButton = document.createElement("button");
  newChatButton.setAttribute("id", "docq-floating-action-button");
  newChatButton.setAttribute("class", "docq-floating-action-button");
  newChatButton.innerHTML = `${icon}`;
  newChatButton.addEventListener("click", () => {
    const btns = __parent.querySelectorAll('button[kind="primary"]');
    const newChatBtn = Array.from(btns).find((btn) => btn.innerText.toLowerCase() === key.toLowerCase());
    if (newChatBtn) {
      newChatBtn.click();
    } else {
      console.log("New chat button not found", newChatBtn, key, icon);
    }
  });
  return newChatButton;
}


function tooltipSetup (label) {
  const newChatTooltip = document.createElement("span");
  newChatTooltip.setAttribute("id", "docq-fab-tooltip");
  newChatTooltip.setAttribute("class", "docq-fab-tooltip");
  newChatTooltip.innerHTML = label;
  return newChatTooltip;
}

previousFabButton = __parent.getElementById("docq-floating-action-button");
if (previousFabButton) {
  previousFabButton.remove();
}

if (!matchParamNotSet.test(fab_config)) {
  const { icon, label, key } = JSON.parse(fab_config)
  const newChatButton = fabSetup(key, icon)
  const newChatTooltip = tooltipSetup(label)
  fabContainer.appendChild(newChatTooltip);
  fabContainer.appendChild(newChatButton);
  if(authState === "authenticated") {
    __parent.body.appendChild(fabContainer);
  }
}

// === END Floating action button =======================

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
