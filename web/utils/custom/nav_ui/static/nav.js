parent = window.parent.document || window.document

const findSideBar = () => {
  const sideBar = parent.querySelectorAll('section[data-testid="stSidebar"]');
  console.log(`sideBar: ${sideBar}, body: ${parent.body}`);
  if (sideBar) {
    return sideBar[0];
  }
    return null;    
}

// Container for the logo
const docqLogoContainer = document.createElement('div');
docqLogoContainer.setAttribute('class', 'docq-logo-container');
docqLogoContainer.setAttribute('id', 'docq-logo-container');
docqLogoContainer.setAttribute('style', 'display: flex; justify-content: center; align-items: center; width: 100%; position: sticky; top: 0; z-index: 1000; background-color: red; flex-direction: column; padding: 10px;');


// Close button
const closeButton = document.createElement('button');
closeButton.setAttribute('id', 'docq-close-button');
closeButton.setAttribute('style', 'position: absolute; right: 10px; top: 10px; background-color: transparent; border: none; outline: none; cursor: pointer;');
closeButton.setAttribute('onclick', 'docqClose()');
closeButton.innerText = 'X';

docqLogoContainer.appendChild(closeButton);


// Logo
const docqLogo = document.createElement('img');
docqLogo.setAttribute('src', 'https://github.com/docqai/docq/blob/main/docs/assets/logo.jpg?raw=true');
docqLogo.setAttribute('alt', 'docq logo');
docqLogo.setAttribute('style', 'width: 50px; height: 50px;');
docqLogo.setAttribute('id', 'docq-logo')
docqLogo.setAttribute('async', '1')


docqLogoContainer.appendChild(docqLogo);


// Create a dropdown menu
const menuTitle = document.createElement('label');
menuTitle.setAttribute('for', 'docq-menu');
menuTitle.innerText = 'Select Organization:';

const dropdownMenu = document.createElement('select');
dropdownMenu.setAttribute('name', 'docq-menu');
dropdownMenu.setAttribute('id', 'docq-menu');
dropdownMenu.setAttribute('style', 'width: 100%; height: 40px; padding: 10px; border-radius: 5px; border: 1px solid #ccc; margin-top: 10');

const options = JSON.parse('{{org-menu-options}}');
options.forEach((option) => {
  const optionElement = document.createElement('option');
  optionElement.setAttribute('value', option.value);
  optionElement.innerText = option.label;
  dropdownMenu.appendChild(optionElement);
});

docqLogoContainer.appendChild(menuTitle);
docqLogoContainer.appendChild(dropdownMenu);


const sideBar = findSideBar();


// Add close script to parent
const closeScript = document.createElement('script');
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
  const docqLogo = parent.getElementById('docq-logo-container');
    if (docqLogo) {
      docqLogo.remove();
    }
  sideBar.insertBefore(docqLogoContainer, sideBar.firstChild);
}
