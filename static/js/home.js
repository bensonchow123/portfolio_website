$(function() {
  $(".typed").typed({
    strings: [
      "cat benson.txt<br/>" +
      "Hobbies: programming, audiophilia, 3D printing, VR, keyboard building<br/> ^100" +
      "Organisation: Year 1 at <a href='https://www.york.ac.uk/'>University of York</a><br/>" +
      "<span class='user'>benson</span><span class='at'>@</span><span class='path'>my-computer</span><span class='caret'>:~$</span>"
    ],
    showCursor: true,
    cursorChar: '|',
    autoInsertCss: true,
    typeSpeed: 0.001,
    startDelay: 10,
    loop: false,
  });
});
