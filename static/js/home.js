$(function() {
  $(".typed").typed({
    strings: [
      "stat benson.human<br/>" +
      "><span class='caret'>$</span> Hobbies: programming, audiophilia, 3D printing, virtual reality, mechanical keyboard building<br/> ^100" +
      "><span class='caret'>$</span> Organisation: Year 1 at <a href='https://www.york.ac.uk/'>University of york</a><br/>" +
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
