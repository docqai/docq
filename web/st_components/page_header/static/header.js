
// Container
const docqContainer = document.createElement("div");
docqContainer.setAttribute("id", "docq-header-container");
docqContainer.setAttribute(
  "style",
  `display: flex; justify-content: center
  align-items: flex-end; position: sticky;
  top: 0; z-index: 1000; background-color: transparent; left: 0;
  flex-direction: column; padding: 10px; gap: 10px;
  width: 50%; height: 50px;
  `
);


// Avatar
const loadAvatar = () => {
  const avatar = document.createElement("img");
  avatar.setAttribute("src", "{{avatar-src}}");
  avatar.setAttribute("alt", "user avatar");
  avatar.setAttribute("style", "width: 25px; height: 25px; border-radius: 50%;");
  avatar.setAttribute("id", "docq-avatar");
  avatar.setAttribute("async", "1");
  return avatar;
}

// Avatar container
const avatarContainer = document.createElement("div");
avatarContainer.setAttribute("id", "docq-avatar-container");
avatarContainer.setAttribute(
  "style",
  "position: absolute; right: 10px; top: 10px; background-color: transparent; border: none; outline: none; cursor: pointer;"
);
avatarContainer.setAttribute("onclick", "docqToggle()");
avatarContainer.appendChild(loadAvatar());


// User name
const userName = document.createElement("span");
userName.innerHTML = "<strong>{{username}}@{{org}}</strong>";
userName.setAttribute("id", "docq-user-name");
userName.setAttribute("style", "margin-right: 20px; margin-left: 16px; width: 100px; text-align: right;");


avatarContainer.appendChild(userName);

docqContainer.appendChild(avatarContainer);

// Insert docq container in the DOM
stApp = window.parent.document.querySelector("header[data-testid='stHeader']");
if (stApp) {
  const prevDocqContainer = window.parent.document.getElementById("docq-header-container");
  if (prevDocqContainer) {
    prevDocqContainer.remove();
  }
  stApp.insertBefore(docqContainer, stApp.firstChild);
}

