<?php

require_once __DIR__ . '/context-policy.php';

tej_apply_public_cqp_policy($_GET, $_POST, $user ?? array());

include $ttroot . '/common/Sources/cqp.php';
