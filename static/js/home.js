$(function() {
  $(".typed").typed({
    strings: [
      "stat benson.human<br/>" +
      "><span class='caret'>$</span> Proficient in: Python, JavaScript, HTML, CSS ^100<br/>" +
      "><span class='caret'>$</span> Hobbies: audiophilia, 3D printing, building mechanical keyboards, making coffee<br/> ^100" +
      "><span class='caret'>$</span> Organisation: Year 13 at <a href='https://www.malverncollege.org.uk/'>Malvern College</a><br/>" +
      ">"
    ],
    showCursor: false,
    cursorChar: '_',
    autoInsertCss: true,
    typeSpeed: 0.001,
    startDelay: 10,
    loop: false,
    onStart: function() { $('.message form').hide(); },
    onStop: function() { $('.message form').show(); },
    onTypingResumed: function() { $('.message form').hide(); },
    onTypingPaused: function() { $('.message form').show(); },
    onComplete: function() { $('.message form').show(); },
    onStringTyped: function() { $('.message form').show(); },
  });
  $('.message form').hide();
});
