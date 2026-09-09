use regex::Regex;
use super::elements::*;

pub struct FountainParser {
    scene_heading_re: Regex,
    forced_scene_re: Regex,
    character_re: Regex,
    forced_character_re: Regex,
    transition_re: Regex,
    forced_transition_re: Regex,
    section_re: Regex,
    synopsis_re: Regex,
    centered_re: Regex,
    page_break_re: Regex,
    scene_number_re: Regex,
    note_re: Regex,
    boneyard_re: Regex,
    lyric_re: Regex,
}

impl FountainParser {
    pub fn new() -> Self {
        Self {
            scene_heading_re: Regex::new(r"^(INT\.|EXT\.|EST\.|INT\./EXT\.|INT/EXT\.|I/E\.)(.*)$").unwrap(),
            forced_scene_re: Regex::new(r"^\.(.+)$").unwrap(),
            character_re: Regex::new(r"^([A-Z][A-Z0-9 \-'.]+?)(\s*\(.*\))?(\s*\^)?$").unwrap(),
            forced_character_re: Regex::new(r"^@(.+)$").unwrap(),
            transition_re: Regex::new(r"^([A-Z ]+TO:)\s*$").unwrap(),
            forced_transition_re: Regex::new(r"^>([^<].*)$").unwrap(),
            section_re: Regex::new(r"^(#{1,6})\s*(.+)$").unwrap(),
            synopsis_re: Regex::new(r"^=\s*(.+)$").unwrap(),
            centered_re: Regex::new(r"^>(.+)<$").unwrap(),
            page_break_re: Regex::new(r"^={3,}\s*$").unwrap(),
            scene_number_re: Regex::new(r"#([^#]+)#\s*$").unwrap(),
            note_re: Regex::new(r"\[\[([^\]]*)\]\]").unwrap(),
            boneyard_re: Regex::new(r"/\*[\s\S]*?\*/").unwrap(),
            lyric_re: Regex::new(r"^~(.+)$").unwrap(),
        }
    }

    pub fn parse(&self, input: &str) -> FountainDocument {
        let cleaned = self.boneyard_re.replace_all(input, "").to_string();
        let lines: Vec<&str> = cleaned.lines().collect();
        let mut elements = Vec::new();
        let mut i = 0;
        let mut title_page = None;

        if let Some((tp, consumed)) = self.parse_title_page(&lines) {
            title_page = Some(tp);
            i = consumed;
        }

        while i < lines.len() {
            let line = lines[i].trim_end();

            if line.is_empty() {
                elements.push(Element::BlankLine);
                i += 1;
                continue;
            }

            if self.page_break_re.is_match(line) {
                elements.push(Element::PageBreak);
                i += 1;
                continue;
            }

            if let Some(caps) = self.section_re.captures(line) {
                let level = caps[1].len() as u8;
                let text = caps[2].trim().to_string();
                elements.push(Element::Section { level, text });
                i += 1;
                continue;
            }

            if let Some(caps) = self.synopsis_re.captures(line) {
                elements.push(Element::Synopsis { text: caps[1].trim().to_string() });
                i += 1;
                continue;
            }

            if let Some(caps) = self.lyric_re.captures(line) {
                elements.push(Element::Lyric { text: caps[1].trim().to_string() });
                i += 1;
                continue;
            }

            if let Some(caps) = self.centered_re.captures(line) {
                elements.push(Element::Action {
                    text: caps[1].trim().to_string(),
                    centered: true,
                    forced: false,
                });
                i += 1;
                continue;
            }

            if let Some(caps) = self.forced_transition_re.captures(line) {
                if !line.ends_with('<') {
                    elements.push(Element::Transition {
                        text: caps[1].trim().to_string(),
                        forced: true,
                    });
                    i += 1;
                    continue;
                }
            }

            if self.transition_re.is_match(line) {
                let prev_blank = elements.last().map_or(true, |e| matches!(e, Element::BlankLine));
                let next_blank = lines.get(i + 1).map_or(true, |l| l.trim().is_empty());
                if prev_blank && next_blank {
                    elements.push(Element::Transition {
                        text: line.trim().to_string(),
                        forced: false,
                    });
                    i += 1;
                    continue;
                }
            }

            if let Some((heading, scene_num, forced)) = self.try_scene_heading(line) {
                elements.push(Element::SceneHeading {
                    text: heading,
                    scene_number: scene_num,
                    forced,
                });
                i += 1;
                continue;
            }

            if let Some(note_text) = self.try_standalone_note(line) {
                elements.push(Element::Note { text: note_text });
                i += 1;
                continue;
            }

            if let Some((char_elem, dialogue_elements, consumed)) = self.try_dialogue_block(&lines, i, &elements) {
                elements.push(char_elem);
                for de in dialogue_elements {
                    elements.push(de);
                }
                i = consumed;
                continue;
            }

            elements.push(Element::Action {
                text: line.to_string(),
                centered: false,
                forced: line.starts_with('!'),
            });
            i += 1;
        }

        FountainDocument {
            elements,
            title_page,
        }
    }

    fn parse_title_page(&self, lines: &[&str]) -> Option<(TitlePage, usize)> {
        let mut pairs: Vec<(String, String)> = Vec::new();
        let mut i = 0;

        if lines.is_empty() || !lines[0].contains(':') {
            return None;
        }

        while i < lines.len() {
            let line = lines[i];
            if line.trim().is_empty() {
                i += 1;
                break;
            }
            if let Some(colon_pos) = line.find(':') {
                let key = line[..colon_pos].trim().to_lowercase();
                let mut value = line[colon_pos + 1..].trim().to_string();
                i += 1;
                while i < lines.len() && (lines[i].starts_with("   ") || lines[i].starts_with('\t')) {
                    if !value.is_empty() {
                        value.push('\n');
                    }
                    value.push_str(lines[i].trim());
                    i += 1;
                }
                pairs.push((key, value));
            } else {
                break;
            }
        }

        if pairs.is_empty() {
            return None;
        }

        let find = |key: &str| pairs.iter().find(|(k, _)| k == key).map(|(_, v)| v.clone());

        Some((
            TitlePage {
                title: find("title"),
                credit: find("credit"),
                author: find("author").or_else(|| find("authors")),
                source: find("source"),
                draft_date: find("draft date"),
                contact: find("contact"),
                copyright: find("copyright"),
            },
            i,
        ))
    }

    fn try_scene_heading(&self, line: &str) -> Option<(String, Option<String>, bool)> {
        if let Some(caps) = self.forced_scene_re.captures(line) {
            let text = caps[1].to_string();
            let scene_num = self.extract_scene_number(&text);
            let heading = self.scene_number_re.replace(&text, "").trim().to_string();
            return Some((heading, scene_num, true));
        }

        if let Some(_caps) = self.scene_heading_re.captures(line) {
            let scene_num = self.extract_scene_number(line);
            let heading = self.scene_number_re.replace(line, "").trim().to_string();
            return Some((heading, scene_num, false));
        }

        None
    }

    fn extract_scene_number(&self, text: &str) -> Option<String> {
        self.scene_number_re.captures(text).map(|c| c[1].trim().to_string())
    }

    fn try_standalone_note(&self, line: &str) -> Option<String> {
        let trimmed = line.trim();
        if trimmed.starts_with("[[") && trimmed.ends_with("]]") {
            Some(trimmed[2..trimmed.len() - 2].to_string())
        } else {
            None
        }
    }

    fn try_dialogue_block(
        &self,
        lines: &[&str],
        start: usize,
        prev_elements: &[Element],
    ) -> Option<(Element, Vec<Element>, usize)> {
        let line = lines[start].trim_end();

        let prev_blank = prev_elements.last().map_or(true, |e| matches!(e, Element::BlankLine));
        if !prev_blank {
            return None;
        }

        let (name, extension, dual, forced) = if let Some(caps) = self.forced_character_re.captures(line) {
            let full = caps[1].trim();
            let dual = full.ends_with('^');
            let clean = if dual { full[..full.len()-1].trim() } else { full };
            let (n, ext) = self.split_character_extension(clean);
            (n, ext, dual, true)
        } else if let Some(caps) = self.character_re.captures(line) {
            let name = caps[1].trim().to_string();
            let ext = caps.get(2).map(|m| m.as_str().trim().to_string());
            let dual = caps.get(3).is_some();
            (name, ext, dual, false)
        } else {
            return None;
        };

        let mut i = start + 1;
        if i >= lines.len() || lines[i].trim().is_empty() {
            return None;
        }

        let char_elem = Element::Character { name, extension, dual, forced };
        let mut dialogue_elems = Vec::new();

        while i < lines.len() {
            let dline = lines[i];
            if dline.trim().is_empty() {
                break;
            }
            let trimmed = dline.trim();
            if trimmed.starts_with('(') && trimmed.ends_with(')') {
                dialogue_elems.push(Element::Parenthetical { text: trimmed.to_string() });
            } else {
                dialogue_elems.push(Element::Dialogue { text: dline.to_string() });
            }
            i += 1;
        }

        if dialogue_elems.is_empty() {
            return None;
        }

        Some((char_elem, dialogue_elems, i))
    }

    fn split_character_extension(&self, s: &str) -> (String, Option<String>) {
        if let Some(paren) = s.find('(') {
            let name = s[..paren].trim().to_string();
            let ext = s[paren..].trim().to_string();
            (name, Some(ext))
        } else {
            (s.to_string(), None)
        }
    }

    pub fn compute_stats(&self, doc: &FountainDocument) -> ScriptStats {
        let mut scenes: Vec<SceneInfo> = Vec::new();
        let mut characters: std::collections::HashMap<String, CharacterInfo> = std::collections::HashMap::new();
        let mut total_words = 0u32;
        let mut dialogue_words = 0u32;
        let mut action_words = 0u32;
        let mut current_scene_idx: Option<usize> = None;
        let mut current_char: Option<String> = None;
        let mut page = 1u32;
        let mut lines_on_page = 0u32;
        let lines_per_page = 55u32;

        for elem in &doc.elements {
            match elem {
                Element::SceneHeading { text, scene_number, .. } => {
                    let idx = scenes.len();
                    scenes.push(SceneInfo {
                        index: idx,
                        number: scene_number.clone(),
                        heading: text.clone(),
                        page,
                        word_count: 0,
                        character_names: Vec::new(),
                    });
                    current_scene_idx = Some(idx);
                    current_char = None;
                    lines_on_page += 2;
                }
                Element::Character { name, .. } => {
                    current_char = Some(name.clone());
                    let entry = characters.entry(name.clone()).or_insert_with(|| CharacterInfo {
                        name: name.clone(),
                        line_count: 0,
                        word_count: 0,
                        scenes: Vec::new(),
                    });
                    if let Some(si) = current_scene_idx {
                        if !entry.scenes.contains(&si) {
                            entry.scenes.push(si);
                        }
                        if let Some(scene) = scenes.get_mut(si) {
                            if !scene.character_names.contains(name) {
                                scene.character_names.push(name.clone());
                            }
                        }
                    }
                    lines_on_page += 1;
                }
                Element::Dialogue { text } => {
                    let wc = text.split_whitespace().count() as u32;
                    total_words += wc;
                    dialogue_words += wc;
                    if let Some(ref cn) = current_char {
                        if let Some(ci) = characters.get_mut(cn) {
                            ci.line_count += 1;
                            ci.word_count += wc;
                        }
                    }
                    if let Some(si) = current_scene_idx {
                        if let Some(scene) = scenes.get_mut(si) {
                            scene.word_count += wc;
                        }
                    }
                    lines_on_page += 1;
                }
                Element::Action { text, .. } => {
                    let wc = text.split_whitespace().count() as u32;
                    total_words += wc;
                    action_words += wc;
                    if let Some(si) = current_scene_idx {
                        if let Some(scene) = scenes.get_mut(si) {
                            scene.word_count += wc;
                        }
                    }
                    lines_on_page += (text.len() as u32 / 60).max(1);
                }
                Element::Parenthetical { .. } => { lines_on_page += 1; }
                Element::Transition { .. } => { lines_on_page += 1; }
                Element::PageBreak => {
                    page += 1;
                    lines_on_page = 0;
                }
                _ => {}
            }

            if lines_on_page >= lines_per_page {
                page += 1;
                lines_on_page = 0;
            }
        }

        let total_content = (dialogue_words + action_words).max(1) as f32;
        let mut char_list: Vec<CharacterInfo> = characters.into_values().collect();
        char_list.sort_by(|a, b| b.word_count.cmp(&a.word_count));

        ScriptStats {
            page_count: page,
            word_count: total_words,
            scene_count: scenes.len() as u32,
            character_count: char_list.len() as u32,
            dialogue_percentage: (dialogue_words as f32 / total_content) * 100.0,
            action_percentage: (action_words as f32 / total_content) * 100.0,
            characters: char_list,
            scenes,
        }
    }
}
