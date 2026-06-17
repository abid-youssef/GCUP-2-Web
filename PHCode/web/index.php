<?php

function validate(mixed $input): string {
  if (!is_string($input))          return '';
  if (strlen($input) > 1024)       return '';
  if (preg_match('/[^\x20-\x7E\r\n]/', $input)) return '';
  if (preg_match('*http|data|valid|pattern|\\\\|\*|&|%|@|//*i', $input)) return '';
  return $input;
}

$dbg = $_GET['debug'] ?? '';
if ($dbg !== '') { $label = 'debug:' . $dbg; }

?>
<!DOCTYPE html>
<html>
<body>
<h1>PHCode</h1>
<h3>Source</h3>
<pre><?php echo htmlspecialchars(file_get_contents(__FILE__)); ?></pre>
<h3>Snippet</h3>
<?php echo validate($_GET["snippet"] ?? "<!-- paste a snippet -->")."\n"; ?><?php
      echo htmlspecialchars($_COOKIE["NOTE"] ?? "NOTE_0123456789abcdef"); ?>
</body>
</html>
