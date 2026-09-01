<?php

require_once __DIR__ . '/context-policy.php';

tej_apply_public_context_policy($_GET, $user ?? array());

include $ttroot . '/common/Sources/context.php';
