console.log("index.js loaded");

const imageInput = document.getElementById("image-input");
const previewImageCard = document.getElementById("image-preview-card");
const previewImage = document.getElementById("preview-img");
const previewFilename = document.getElementById("preview-filename");
const cancelbtn = document.querySelector("#cancel-image");

if (imageInput) {
  imageInput.addEventListener("change", (event) => {
    file = event.target.files[0];
    console.log(event);
    previewImage.src = URL.createObjectURL(file);
    previewFilename.textContent = file.name;
    previewImageCard.style.display = "block";
  });

  cancelbtn.addEventListener("click", function () {
    previewImageCard.style.display = "none";
    previewImage.src = "";
    imageInput.value = "";
    previewFilename.textContent = "";
  });
}
