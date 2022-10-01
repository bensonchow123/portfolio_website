$(function() {
  /* NOTE: hard-refresh the browser once you've updated this */
  $(".typed").typed({
    strings: [
      "stat Benson.human<br/>" +
      "><span class='caret'>$</span> languages: Python, Javascript, HTML, CSS<br/>" +
      "><span class='caret'>$</span> school: year 12 at <a href='https://www.malverncollege.org.uk/'>Malvern college</a><br/> ^200" +
      "><span class='caret'>$</span> hobbies: programming, minecraft<br/> ^150" +
      "><span class='caret'>$</span> known as: Hypicksell <br/>"
    ],
    showCursor: true,
    cursorChar: '_',
    autoInsertCss: true,
    typeSpeed: 0.001,
    startDelay: 50,
    loop: false,
    showCursor: false,
    onStart: $('.message form').hide(),
    onStop: $('.message form').show(),
    onTypingResumed: $('.message form').hide(),
    onTypingPaused: $('.message form').show(),
    onComplete: $('.message form').show(),
    onStringTyped: function(pos, self) {$('.message form').show();},
  });
  $('.message form').hide()
});
