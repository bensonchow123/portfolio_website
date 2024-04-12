$(function() {
  $(".typed").typed({
    strings: [
      "stat Benson.human<br/>" +
      "><span class='caret'>$</span> fluent languages: Python, Javascript, HTML, CSS<br/>" +
      "><span class='caret'>$</span> hobbies: audiophile, 3d printing, machanical keyboards <br/> ^150" +
      "><span class='caret'>$</span> school: year 13 at <a href='https://www.malverncollege.org.uk/'>Malvern college</a><br/> ^200"
    ],
    showCursor: false,
    cursorChar: '_',
    autoInsertCss: true,
    typeSpeed: 0.001,
    startDelay: 50,
    loop: false,
    onStart: $('.message form').hide(),
    onStop: $('.message form').show(),
    onTypingResumed: $('.message form').hide(),
    onTypingPaused: $('.message form').show(),
    onComplete: $('.message form').show(),
    onStringTyped: function(pos, self) {$('.message form').show();},
  });
  $('.message form').hide()
});
