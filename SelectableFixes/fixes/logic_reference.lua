-- HUMAN-READABLE REFERENCE; not loaded by build.py or by the game.
-- Exact executable patch sources are the Python files beside this document.
-- RU: Справочное пояснение; сборщик и игра этот файл не загружают.
-- Исполняемые исходники патчей — соседние Python-файлы.

-- Quest hint, normal video-button branch, in BOTH interfaces:
-- RU: Обычная кнопка видео в ОБОИХ интерфейсах квестов.
-- self.levelTarget = buttonMeta.target
-- self.levelTargetQuestId = buttonMeta.questId
-- settingsWrapper:setQuestVideoWatched(buttonMeta.questId)
-- The existing update function displays the hint on the next UI tick.
-- RU: Существующая update показывает подсказку на следующем кадре интерфейса.

-- unlock_all_episodes: only isEpisodeUnlocked returns true.
-- RU: Только isEpisodeUnlocked возвращает true.
-- unlock_all_levels (opt-in): selected access/layout predicates return true;
-- isEpisodeStarLocked returns false; getLastOpenLevel returns sentinel 200.
-- unlock_ragnahog_levels preserves all egg/star/feather predicates.
-- RU: unlock_ragnahog_levels сохраняет проверки яиц, звёзд и перьев.
-- RU: Выбранные проверки доступа/раскладки возвращают true;
-- isEpisodeStarLocked — false, getLastOpenLevel — служебное значение 200.

-- Cosmetics: create/update ONLY the 108 journal collection records.
-- RU: Создать/обновить ТОЛЬКО 108 коллекционных записей журнала.
-- saved.completedQuests = saved.completedQuests or {}
-- for _, frame in ipairs(allShippedJournalFrames) do
--   local id = frame.questId
--   local record = saved.completedQuests[id] or {}
--   saved.completedQuests[id] = record
--   record.completed = true
--   record.collectedStamps = copyArray(questDefinitions[id].questTargets or {})
--   record.currentItem = math.max(1, #record.collectedStamps)
-- end
-- Calls from isCompletedQuest/getCompletedQuest ensure these records exist.
-- RU: isCompletedQuest/getCompletedQuest сначала обеспечивают наличие записей.

-- Coins: one-time top-up, kept in the SAME private settings upvalue.
-- RU: Однократное пополнение в ТОЙ ЖЕ приватной таблице настроек upvalue.
local function coinReference(saved, configured_amount)
  local amount = saved.IngameCurrencyAmount or 0
  if not saved.__seasons_selectable_fixes_coins_v1 then
    if amount < configured_amount then
      amount = configured_amount
      saved.IngameCurrencyAmount = amount
    end
    saved.__seasons_selectable_fixes_coins_v1 = true
  end
  return amount
end

-- unlock_ragnahog_levels: JSON page index 0 (Lua page index 1).
-- RU: Ragnahog: индекс страницы JSON 0 (в Lua — 1).
-- episodes.episodeRagnahog.pages[1].all_levels_open = true
-- episodes.episodeRagnahog.manual_level_progression = false
return coinReference
