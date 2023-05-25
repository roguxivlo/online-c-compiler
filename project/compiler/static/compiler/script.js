// Autor: Jan Roguwski
function toggleStyle() {
  var element = document.body;
  element.classList.toggle("light-mode");
  element.classList.toggle("dark-mode");
}

function openTab(evt, tabName) {
  var i, tabcontent, tablinks;
  tabcontent = document.getElementsByClassName("tabs-text");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }
  tablinks = document.getElementsByClassName("tab_button");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }
  document.getElementById(tabName).style.display = "block";
  evt.currentTarget.className += " active";
}

function showCompiled(file_pk) {
  let code = document.getElementById("code");
  let url = "/compiler/compile/" + file_pk;
  fetch(url)
    .then(response => response.text())
    .then(data => {
      code.innerHTML = data;
    });
}

function showFile(file_pk) {
  let main = document.getElementById("main");
  // main.innerHTML = "plik numer " + file_pk;
  let url = "/compiler/showfile/" + file_pk;
  fetch(url)
    .then(response => response.text())
    .then(data => {
      main.innerHTML = data;
    });
    showCompiled(file_pk);
}

function showFiles() {
  let sidebar = document.getElementById("sidebar");
  let url = "/compiler/generate_file_tree_html/";
  fetch(url)
    .then(response => response.text())
    .then(data => {
      sidebar.innerHTML = data;
    });
}

function addFile() {
  showFiles();
  let main = document.getElementById("main");
  fetch("/compiler/addFileForm")
    .then(response => response.text())
    .then(data => {
      main.innerHTML = data;
    });

}

function addDirectory() {
  showFiles();
  let main = document.getElementById("main");
  fetch("/compiler/addDirectoryForm")
    .then(response => response.text())
    .then(data => {
      main.innerHTML = data;
    });
}

function deleteFile(file_pk) {
  let url = "/compiler/delete_file/" + file_pk;
  fetch(url)
    .then(response => showFiles());
}

function deleteDirectory(file_pk) {
  let url = "/compiler/delete_directory/" + file_pk;
  fetch(url)
    .then(response => showFiles());
}

function highlightCCodeLine(lineId, caller) {
  // get div with id "main", and then inside it,
  // get div with id lineId:
  let line = document.getElementById("main").querySelector("#" + "l" + lineId);
  // modify line background color. toggle between two colors
  line.classList.toggle("highlighted");
  // toggle highlight calling element:
  caller.classList.toggle("highlighted");
  console.log(line);
}

function collapseASMSection(sectionId, isParent) {
  // Only execute if isParent is true:
  if (isParent == "True") {
    // get all elements with data-section attribute equal to sectionId and isParent
    // is false:
    let elements = document.querySelectorAll("[data-section='" + sectionId + "'][data-isParent='False']");
    // toggle display of all elements:
    elements.forEach(element => {
      element.classList.toggle("hidden");
    });
  }
}
