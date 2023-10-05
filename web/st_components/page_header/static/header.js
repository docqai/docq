
// Container
const docqContainer = document.createElement("div");
docqContainer.setAttribute("id", "docq-header-container");
docqContainer.setAttribute(
  "style",
  "display: flex; justify-content: center; align-items: flex-start; position: sticky; top: 0; z-index: 1000; background-color: red; flex-direction: column; padding: 10px; gap: 10px;"
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
const userName = document.createElement("p");
userName.innerText = "{{username}}";
userName.setAttribute("id", "docq-user-name");
userName.setAttribute("style", "margin-right: 10px;");

parent.addEventListener("load", () => {
    const avatar = loadAvatar();
    avatarContainer.appendChild(avatar);
    });


docqContainer.appendChild(avatarContainer);
docqContainer.appendChild(userName);

// Insert docq container in the DOM
const headerBar = parent.document.querySelector("header");
if (headerBar) {
    headerBar.insertBefore(docqContainer, headerBar.firstChild);
}

