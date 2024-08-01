import Typewriter from 'typewriter-effect/dist/core';
import JSConfetti from 'js-confetti';
import './style.css';
import Master from './master_nocolor.png';
import Leadpic from './leadpic.png';
import Logo from './logo.svg';
import AvitoLogo from './avito.svg';
import VKLogo from './vk.svg';
import TGLogo from './telegram.svg';
import naberezhnaya from './naberezhnaya.jpg';
import notfound from './404.png'
import dvor from './dvor.jpg'

// svistoperdelki

if (window.location.pathname == "/") {

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
  addPic("leadpic", Leadpic);

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
  }

// form validation

class Validator {
  constructor() {
    this.validationPassed = true;
  }

  static emailValidate(contact) {
    return String(contact)
      .toLowerCase()
      .match(
        /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
      );
  };

  static socialNetworksValidate(contact) {
    return String(contact)
    .toLowerCase()
    .match(
      /^([A-Za-z0-9_]{3,25})$/
    );
  }
  
  static phoneValidate(contact) {
    return String(contact)
    .toLowerCase()
    .match(
      /^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$/
    );
  }

  validate(selectedOption, contact) {
    const toggleValidationWarning = (elem, callback) => {
      if (callback(elem.value) == null) {
        addValidationWarning(elem);
        return;
      }
      removeValidationWarnig(elem);
    }
    
    const addValidationWarning = (element) => {
      this.validationPassed = false;
      element.classList.add("form-control", "is-invalid");
      if (this.label === undefined) {
        this.label = document.createElement('div');
        this.label.classList.add("invalid-feedback", "text-start");
        this.label.innerHTML += "Пожалуйста, проверьте данные";
      
        contact.parentNode.insertBefore(this.label, element.nextSibling);
      }
    }
    
    const removeValidationWarnig = (element) => {
        this.validationPassed = true;
        if (!(this.label === undefined)) {
          element.classList.remove("is-invalid");
          element.classList.add("is-valid");
          this.label.remove();
        }
    }

    switch (selectedOption) {
      case "not-selected":
        alert("Пожалуйста, выберите платформу для свзяи");
        break;
      case "email":
        toggleValidationWarning(contact, this.constructor.emailValidate);
        break;
      case "phone":
        toggleValidationWarning(contact, this.constructor.phoneValidate);
        break;
      default:
        toggleValidationWarning(contact, this.constructor.socialNetworksValidate);
    }
    console.log(this)
  }
}

if (window.location.href.includes("repair_order") || window.location.pathname == "/") {
  let validator = new Validator();
  document.getElementById("formButton").addEventListener('click', async () => {
    let contact = document.getElementById("contact");
    let selectedOption = document.getElementById("socSelect").selectedOptions[0].value;
    validator.validate(selectedOption, contact);

    if (validator.validationPassed) {
      let answer = new FormData(document.getElementById("form"));
      answer.append("soc_type", selectedOption);
      await fetch("form", {
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
    }
  }) 
}

if (window.location.href.includes("tracking")) {
  let form = document.getElementById("form");
  try {
    document.getElementById("formButton").addEventListener('click', async (e) => {
      let userInput = document.getElementById("order-uuid");
      if (userInput.value.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i)) {
        await fetch("/tracking/is_exist", {
          method: 'POST',
              headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
              },
              body: userInput.value
        }).then(res => {
          if (res.status == 200) {
            let uuid = userInput.value;
            form.reset();
            document.location += uuid; 
          }})
      }
      userInput.classList.add("form-control", "is-invalid");
      if (userInput.label === undefined) {
        userInput.label = document.createElement('div');
        userInput.label.classList.add("invalid-feedback", "text-start");
        userInput.label.innerHTML += "Пожалуйста, проверьте данные";
      
        userInput.parentNode.insertBefore(userInput.label, userInput.nextSibling);
      }
    });
  } catch (e) {
    console.log(e)
  }

  if (document.getElementById("status").children[0].innerText == "Готов") {
    const jsConfetti = new JSConfetti();
    jsConfetti.addConfetti({
      emojis: ['📷', '🪛', '⚙️', '✨', '🔋', '🧑‍🏭', '📸'],
   })
  }
}