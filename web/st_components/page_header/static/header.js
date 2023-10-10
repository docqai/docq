// PAGE-HEADER-SCRIPT === DO NOT REMOVE THIS COMMENT --- Used to identify this script in the page header
parent = window.parent.document || window.document;

// Get params === These are to be set in the template by the method that loads this script
const username = `{{username}}`; // User name to be displayed in the header
const avatarSrc = `{{avatar_src}}`; // Avatar image source
const menuItemsJson = `{{menu_items_json}}`; // [{ "text": "Menu item text", "key": "menu-item-button-key", "icon": "menu-item-icon-html"}]
const styleDoc = `{{style_doc}}`; // CSS string to be added to the parent.document.head
const fab_config = `{{fab_config}}`; // { "icon": "fab-icon", "label": "tool-tip-text", "key": "fab-button-key" }
const authState = `{{auth_state}}`; // "authenticated" or "unauthenticated"

const matchParamNotSet = /\{\{.*\}\}/;

const defaultMenuItemIcon = `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M21 12L13 12" stroke="#323232" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> <path d="M18 15L20.913 12.087V12.087C20.961 12.039 20.961 11.961 20.913 11.913V11.913L18 9" stroke="#323232" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> <path d="M16 5V4.5V4.5C16 3.67157 15.3284 3 14.5 3H5C3.89543 3 3 3.89543 3 5V19C3 20.1046 3.89543 21 5 21H14.5C15.3284 21 16 20.3284 16 19.5V19.5V19" stroke="#323232" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> </g></svg>`


// Add style to the parent document head
if (!matchParamNotSet.test(styleDoc)) {
  const style = parent.createElement("style");
  style.setAttribute("id", "docq-header-style");
  // check if style tag already exists and verify if it is the same as the one to be added
  const prevStyle = parent.getElementById("docq-header-style");
  if (prevStyle && prevStyle.innerHTML !== styleDoc) {
    prevStyle.innerHTML = styleDoc;
  } else {
    style.innerHTML = styleDoc;
    parent.head.appendChild(style);
  }  
}


/** Utility functions */// ==========================================================================================================================================================

/**
 * Inserts a class to the svg element in the menu item html
 * @param {string} menuItemHtml  The html string of the menu item
 * @param {string} iconClass Icon class to be added to the svg element (default: 'docq-user-menu-item-icon')
 * @returns {string} The html string of the menu item with the icon class added to the svg element
 */
function insertUserMenuItemIconClass(menuItemHtml, iconClass = 'docq-user-menu-item-icon'){
  const parser = new DOMParser()
  const doc = parser.parseFromString(menuItemHtml, 'text/html')
  const svg = doc.querySelector('svg')
  svg.setAttribute('class', iconClass)
  return doc.body.innerHTML
}

/**
 * Creates a user menu item using the given text and icon html string 
 * @param {string} text The text to be displayed in the menu item
 * @param {string} imgHtml 
 * @returns {HTMLButtonElement} The user menu item
 */
function createUserMenuItem(text, imgHtml = null){
  const item = parent.createElement('button')
  item.setAttribute('class', 'docq-user-menu-item')
  item.setAttribute('id', `docq-user-menu-item-${text.replace(' ', '-')}`)
  if (imgHtml) {
    const iconWithClass = insertUserMenuItemIconClass(imgHtml)
    item.innerHTML = `<span>${iconWithClass}${text}</span>`
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
  const divider = parent.createElement('div')
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
const logoutImgHtml = `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M21 12L13 12" stroke="#323232" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> <path d="M18 15L20.913 12.087V12.087C20.961 12.039 20.961 11.961 20.913 11.913V11.913L18 9" stroke="#323232" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> <path d="M16 5V4.5V4.5C16 3.67157 15.3284 3 14.5 3H5C3.89543 3 3 3.89543 3 5V19C3 20.1046 3.89543 21 5 21H14.5C15.3284 21 16 20.3284 16 19.5V19.5V19" stroke="#323232" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> </g></svg>`
const logoutBtn = createUserMenuItem("Logout", logoutImgHtml)
logoutBtn.addEventListener("click", () => {
  const btns = parent.querySelectorAll('button[kind="primary"]');
  const logoutBtn = Array.from(btns).find((btn) => btn.innerText === "Logout");
  if (logoutBtn) {
    logoutBtn.click();
  } else {
    console.log("Logout button not found", logoutBtn);
  }
})

/** Help and Feedback section */
// Help =====================================================================================
const helpSvgHtml = `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M23 12C23 18.0751 18.0751 23 12 23C5.92487 23 1 18.0751 1 12C1 5.92487 5.92487 1 12 1C18.0751 1 23 5.92487 23 12ZM3.00683 12C3.00683 16.9668 7.03321 20.9932 12 20.9932C16.9668 20.9932 20.9932 16.9668 20.9932 12C20.9932 7.03321 16.9668 3.00683 12 3.00683C7.03321 3.00683 3.00683 7.03321 3.00683 12Z" fill="#0F0F0F"></path> <path d="M13.5 18C13.5 18.8284 12.8284 19.5 12 19.5C11.1716 19.5 10.5 18.8284 10.5 18C10.5 17.1716 11.1716 16.5 12 16.5C12.8284 16.5 13.5 17.1716 13.5 18Z" fill="#0F0F0F"></path> <path d="M11 12V14C11 14 11 15 12 15C13 15 13 14 13 14V12C13 12 13.4792 11.8629 13.6629 11.7883C13.6629 11.7883 13.9969 11.6691 14.2307 11.4896C14.4646 11.3102 14.6761 11.097 14.8654 10.8503C15.0658 10.6035 15.2217 10.3175 15.333 9.99221C15.4443 9.66693 15.5 9.4038 15.5 9C15.5 8.32701 15.3497 7.63675 15.0491 7.132C14.7596 6.61604 14.3476 6.21786 13.8132 5.93745C13.2788 5.64582 12.6553 5.5 11.9427 5.5C11.4974 5.5 11.1021 5.55608 10.757 5.66825C10.4118 5.7692 10.1057 5.9094 9.83844 6.08887C9.58236 6.25712 9.36525 6.4478 9.18711 6.66091C9.02011 6.86281 8.8865 7.0591 8.78629 7.24978C8.68609 7.44046 8.61929 7.6087 8.58589 7.75452C8.51908 7.96763 8.49125 8.14149 8.50238 8.27609C8.52465 8.41069 8.59145 8.52285 8.70279 8.61258C8.81413 8.70231 8.9867 8.79765 9.22051 8.8986C9.46546 8.97712 9.65473 9.00516 9.78834 8.98273C9.93308 8.96029 10.05 8.89299 10.1391 8.78083C10.1391 8.78083 10.6138 8.10569 10.7474 7.97109C10.8922 7.82528 11.0703 7.71312 11.2819 7.6346C11.4934 7.54487 11.7328 7.5 12 7.5C12.579 7.5 13.0076 7.64021 13.286 7.92062C13.5754 8.18982 13.6629 8.41629 13.6629 8.93225C13.6629 9.27996 13.6017 9.56038 13.4792 9.77349C13.3567 9.9866 13.1953 10.1605 12.9949 10.2951C12.9949 10.2951 12.7227 10.3991 12.5 10.5C12.2885 10.5897 11.9001 10.7381 11.6997 10.8503C11.5104 10.9512 11.4043 11.0573 11.2819 11.2144C11.1594 11.3714 11 11.7308 11 12Z" fill="#0F0F0F"></path> </g></svg>`
const helpBtn = createUserMenuItem("Help", helpSvgHtml)
helpBtn.addEventListener("click", () => {
  window.open("https://docq.ai", "_blank");
});

// Send feedback ===========================================================================
const feedbackSvgHtml = `<svg viewBox="0 0 1024 1024" class="icon" version="1.1" xmlns="http://www.w3.org/2000/svg" fill="#000000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path d="M415.808 755.2L512 851.392 608.192 755.2H883.2V204.8H704V128h256v704h-320l-128 128-128-128H64V128h256v76.8H140.8v550.4h275.008zM473.6 64h76.8v448H473.6V64z m0 512h76.8v76.8H473.6V576z" fill="#000000"></path></g></svg>`
const feedbackBtn = createUserMenuItem("Send feedback", feedbackSvgHtml)
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
    const icon = item?.icon || defaultMenuItemIcon
    const menuItem = createUserMenuItem(item.text, icon)
    menuItem.addEventListener('click', () => {
      const btns = parent.querySelectorAll('button[kind="primary"]');
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
console.log("authState", authState);
if (authState === "authenticated") {
  avatarContainer.appendChild(userMenu);
}

// User menu toggle
avatar.addEventListener("click", () => {
  const userMenu = parent.getElementById("docq-user-menu");
  if (userMenu) {
    userMenu.classList.toggle("docq-user-menu-active");
    // Autofocus on the user menu
    const userMenuItems = userMenu.querySelectorAll(".docq-user-menu-item");
    if (userMenuItems.length > 0) {
      userMenuItems[0].focus();
    }

    // Close user menu on click outside
    const closeUserMenu = (e) => {
      if (!userMenu.contains(parent.activeElement)) {
        userMenu.classList.remove("docq-user-menu-active");
        parent.removeEventListener("click", closeUserMenu);
      }
    };
    parent.addEventListener("click", closeUserMenu);
  } else {
    console.log("User menu not found", userMenu);
  }
});

// User menu animation
const userMenuObserver = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.attributeName === "class") {
      const userMenu = parent.getElementById("docq-user-menu");
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
    const userMenu = parent.getElementById("docq-user-menu");
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
    const btns = parent.querySelectorAll('button[kind="primary"]');
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

previousFabButton = parent.getElementById("docq-floating-action-button");
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
    parent.body.appendChild(fabContainer);
  }
}

// === END Floating action button =======================

// Insert docq container in the DOM
stApp = parent.querySelector("header[data-testid='stHeader']");
if (stApp) {
  const prevDocqContainer = parent.getElementById("docq-header-container");
  if (prevDocqContainer) {
    prevDocqContainer.remove();
  }
  stApp.insertBefore(docqContainer, stApp.firstChild);
}


// ===
const iframes = parent.querySelectorAll("iframe");
iframes.forEach((iframe) => {
  const srcdoc = iframe.getAttribute("srcdoc");
  if (srcdoc.includes("PAGE-HEADER-SCRIPT")) {
    iframe.parentNode.setAttribute("class", "docq-iframe-container");
  }
});
