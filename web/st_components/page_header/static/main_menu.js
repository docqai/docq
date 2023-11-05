/**
 * Script for appending items to the user menu
 */

const __document = window.parent.document || window.document;
console.log("main-menu-script", __document);

const mainMenu = __document.querySelectorAll('div[data-testid="main-menu-popover"]')[0];
const sideBar = __document.querySelectorAll('section[data-testid="stSidebar"]')[0];

const secondaryColor = window.getComputedStyle(sideBar, null).getPropertyValue('background-color');


function stringContainsAll(string, substrings) {
  return substrings.every((substring) => string.includes(substring));
}

const userMenu = __document.getElementById("docq-user-menu");

/**
 * Set User menu style
 */
const setUSermenuStyle = () => {
  if (userMenu){
    const backgroundColor = window.getComputedStyle(sideBar, null).getPropertyValue('background-color');
    userMenu.setAttribute("style", `background-color: ${backgroundColor};`);
  }
}

function cloneOrgSelector(id) {
  const orgSelector = sideBar.querySelectorAll('div.row-widget.stSelectbox')[0];
  if (orgSelector) {
    const orgSelectorClone = orgSelector.parentNode.cloneNode(true);
    orgSelectorClone.setAttribute("id", id);
    return orgSelectorClone;
  }
  return null;
}

function createUsermenuItems () {
  if (sideBar && userMenu) {
    setUSermenuStyle();
    const sideBarItems = sideBar.querySelectorAll('li');
    // find admin section index
    const adminSectionIndex = Array.from(sideBarItems).findIndex((item) => stringContainsAll(item.innerText, ["Admin", "💂"]));

    const _index = adminSectionIndex === -1 ? sideBarItems.length : adminSectionIndex;
    const userMenuUL = document.createElement("ul");
    userMenuUL.setAttribute("id", "docq-user-menu-ul")

    sideBarItems.forEach((item, index) => {
      if (index < _index){
        return;
      }
      else {
        userMenuUL.appendChild(item.cloneNode(true));
      }
    });


    const orgSelectorClone = cloneOrgSelector("docq-org-selector");
    const prevSelector = __document.getElementById("docq-org-selector");
    if (prevSelector) {
      prevSelector.remove();
    }
    if (orgSelectorClone) {
      userMenuUL.appendChild(orgSelectorClone);
    }
    


    const prevUL = __document.getElementById("docq-user-menu-ul");
    if (prevUL) {
      prevUL.remove();
    }
    userMenu.appendChild(userMenuUL);
  }
}

createUsermenuItems();

// Observe sidebar style changes and apply to usermenu
const observer = new MutationObserver(createUsermenuItems);
observer.observe(__document.body, { attributes: true, attributeFilter: ['style']});
