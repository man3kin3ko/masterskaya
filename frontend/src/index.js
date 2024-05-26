import Typewriter from 'typewriter-effect/dist/core';
import './style.css';
import Master from './master_nocolor.png';
import Leadpic from './leadpic.png';

function addPic(divId, Img, style=null) {
  const Pic = new Image();
  Pic.src = Img;
  var parent = document.getElementById(divId);
  var pic = parent.insertBefore(Pic, parent.firstChild);
  pic.classList.add("img-fluid", "multiply");
  if (style != null) {
    pic.style.width = style;
  }
}

addPic("master", Master);
addPic("leadpic", Leadpic, "25%");

var app = document.getElementById('typewriter');
var typewriter = new Typewriter(app, {
  loop: true,
  delay: 75,
  autoStart: true
});

typewriter
  .typeString('Exacta')
  .pauseFor(300)
  .deleteAll()
  .typeString('Minolta')
  .pauseFor(300)
  .deleteAll()
  .typeString('Зоркий')
  .pauseFor(300)
  .deleteAll()
  .typeString('ФЭД')
  .pauseFor(300)
  .deleteAll()
  .typeString('Leica')
  .pauseFor(300)
  .deleteAll()
  .typeString('Зенит')
  .pauseFor(300)
  .deleteAll()
  .typeString('Rolleiflex')
  .pauseFor(300)
  .deleteAll()
  .typeString('или даже Bentzin Primar')
  .pauseFor(1500)
  .deleteAll()
  .start();


const emailValidate = (email) => {
  return String(email)
    .toLowerCase()
    .match(
      /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
    );
};

function socialNetworksValidate(contact) {
  console.log(contact);
}

function addValidationWarning(element) {
  element.classList.add("form-control", "is-invalid");

  let label = document.createElement('div');
  label.classList.add("invalid-feedback", "text-start");
  label.innerHTML += "Пожалуйста, проверьте адрес";
  label.setAttribute("id","emailFeedback");

  contact.parentNode.insertBefore(label, element.nextSibling);

}

function removeValidationWarnig(element) {
  element.classList.remove("is-invalid");
  element.classList.add("is-valid");
  try {
    document.getElementById("emailFeedback").remove();
  }
  catch (e) {};
}

document.getElementById("formButton").addEventListener('click', async () => {
  let contact = document.getElementById("contact");
  let selectedOption = document.getElementById("socSelect").selectedOptions[0].value;
  if (selectedOption == "email") {
    if (emailValidate(contact.value) == null) {
      addValidationWarning(contact);
      return;
    }
    else {
      removeValidationWarnig(contact);
    }
  }

  let answer = new FormData(document.getElementById("form"));
  answer.append("soc_type", selectedOption);
  await fetch("http://localhost:8000/form", {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(Object.fromEntries(answer))
    })
    .then(res => {
      if (res.status == 200) { 
        alert("Спасибо за обращение");
        form.reset();
      }
      else {
        console.log(res);
        alert("Что-то пошло не так");
      }
    })
    .catch(err => {
      console.error(err);
      alert("Что-то пошло не так. Попробуйте снова");
    });
    return false;
}) 