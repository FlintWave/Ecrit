use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Dialect {
    pub id: String,
    pub name: String,
    pub description: String,
    pub paper: PaperSize,
    pub extra_elements: Vec<ExtraElement>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub enum PaperSize {
    USLetter,
    A4,
}

impl PaperSize {
    pub fn width_inches(&self) -> f64 {
        match self {
            PaperSize::USLetter => 8.5,
            PaperSize::A4 => 8.27,
        }
    }

    pub fn height_inches(&self) -> f64 {
        match self {
            PaperSize::USLetter => 11.0,
            PaperSize::A4 => 11.69,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExtraElement {
    pub name: String,
    pub tag: String,
}

pub fn builtin_dialects() -> Vec<Dialect> {
    vec![
        Dialect {
            id: "fountain/core".into(),
            name: "Standard Screenplay".into(),
            description: "The modern spec standard — master scenes, Courier Prime 12pt, US Letter.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+shooting".into(),
            name: "Shooting Script".into(),
            description: "Numbered scenes, locked pages, revision colors for production.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+studio47".into(),
            name: "Classic Studio 1930s–50s".into(),
            description: "Vintage studio format with period conventions.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+a4".into(),
            name: "European A4".into(),
            description: "Metric standard — A4 paper with adjusted margins.".into(),
            paper: PaperSize::A4,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+multicam".into(),
            name: "US Multi-Camera Sitcom".into(),
            description: "Multi-camera format with underlined slug lines and double-spaced dialogue.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+bbc-screen".into(),
            name: "BBC Screenplay".into(),
            description: "BBC television screenplay format on A4.".into(),
            paper: PaperSize::A4,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+bbc-scene".into(),
            name: "BBC Scene Style".into(),
            description: "BBC scene-style television format on A4.".into(),
            paper: PaperSize::A4,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+radio-scene".into(),
            name: "BBC Radio Scene Style".into(),
            description: "BBC radio drama in scene style on A4.".into(),
            paper: PaperSize::A4,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+radio-cue".into(),
            name: "BBC Radio Cue Style".into(),
            description: "BBC radio drama with numbered cues on A4.".into(),
            paper: PaperSize::A4,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+audio-us".into(),
            name: "US Audio Drama".into(),
            description: "American audio drama format on US Letter.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+comic-dc".into(),
            name: "DC / Marvel House Style".into(),
            description: "Industry-standard full script — PAGE/PANEL hierarchy, numbered lettering elements, balloon-type parentheticals. Used by DC, Marvel, and most mainstream publishers.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![
                ExtraElement { name: "Page".into(), tag: "page_header".into() },
                ExtraElement { name: "Panel".into(), tag: "panel_header".into() },
                ExtraElement { name: "Caption".into(), tag: "caption".into() },
                ExtraElement { name: "SFX".into(), tag: "sfx".into() },
                ExtraElement { name: "Banner".into(), tag: "banner".into() },
                ExtraElement { name: "Voice Over".into(), tag: "voice_over".into() },
            ],
        },
        Dialect {
            id: "fountain+comic-dh".into(),
            name: "Dark Horse Style".into(),
            description: "Dark Horse house style — heavier panel descriptions, numbered captions and SFX, editorial notes supported. Matches Dark Horse submission guidelines.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![
                ExtraElement { name: "Page".into(), tag: "page_header".into() },
                ExtraElement { name: "Panel".into(), tag: "panel_header".into() },
                ExtraElement { name: "Caption".into(), tag: "caption".into() },
                ExtraElement { name: "SFX".into(), tag: "sfx".into() },
                ExtraElement { name: "Banner".into(), tag: "banner".into() },
                ExtraElement { name: "Editorial".into(), tag: "editorial".into() },
            ],
        },
        Dialect {
            id: "fountain+comic-indie".into(),
            name: "Image / Indie Style".into(),
            description: "Flexible indie format used at Image, BOOM!, and creator-owned books — PAGE/PANEL structure with per-page lettering numbers and all caption subtypes.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![
                ExtraElement { name: "Page".into(), tag: "page_header".into() },
                ExtraElement { name: "Panel".into(), tag: "panel_header".into() },
                ExtraElement { name: "Caption".into(), tag: "caption".into() },
                ExtraElement { name: "SFX".into(), tag: "sfx".into() },
                ExtraElement { name: "Banner".into(), tag: "banner".into() },
                ExtraElement { name: "Voice Over".into(), tag: "voice_over".into() },
                ExtraElement { name: "Internal".into(), tag: "internal".into() },
                ExtraElement { name: "Narration".into(), tag: "narration".into() },
            ],
        },
        Dialect {
            id: "fountain+stage-us".into(),
            name: "US Stage Play".into(),
            description: "American stage play format on US Letter.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![
                ExtraElement { name: "Stage Direction".into(), tag: "stage_dir".into() },
            ],
        },
        Dialect {
            id: "fountain+stage-uk".into(),
            name: "UK Stage Play".into(),
            description: "British stage play format on A4.".into(),
            paper: PaperSize::A4,
            extra_elements: vec![
                ExtraElement { name: "Stage Direction".into(), tag: "stage_dir".into() },
            ],
        },
        Dialect {
            id: "fountain+branch".into(),
            name: "Branching Dialogue".into(),
            description: "Interactive branching dialogue for games.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![
                ExtraElement { name: "Choice".into(), tag: "choice".into() },
                ExtraElement { name: "Branch".into(), tag: "branch".into() },
            ],
        },
        Dialect {
            id: "fountain+barks".into(),
            name: "Barks & Systemic VO".into(),
            description: "Short voice lines and systemic dialogue for games.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![
                ExtraElement { name: "Bark".into(), tag: "bark".into() },
                ExtraElement { name: "Context".into(), tag: "context".into() },
            ],
        },
    ]
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FormatCategory {
    pub name: String,
    pub description: String,
    pub formats: Vec<String>,
}

pub fn format_categories() -> Vec<FormatCategory> {
    vec![
        FormatCategory {
            name: "Feature Film".into(),
            description: "Master-scene screenplays, from the modern spec standard back to the studio-era house styles.".into(),
            formats: vec![
                "fountain/core".into(),
                "fountain+shooting".into(),
                "fountain+studio47".into(),
                "fountain+a4".into(),
            ],
        },
        FormatCategory {
            name: "Television".into(),
            description: "Single-camera drama, multi-camera sitcom, and BBC formats.".into(),
            formats: vec![
                "fountain/core".into(),
                "fountain+multicam".into(),
                "fountain+bbc-screen".into(),
                "fountain+bbc-scene".into(),
            ],
        },
        FormatCategory {
            name: "Audio & Radio".into(),
            description: "BBC radio drama and US audio drama formats.".into(),
            formats: vec![
                "fountain+radio-scene".into(),
                "fountain+radio-cue".into(),
                "fountain+audio-us".into(),
            ],
        },
        FormatCategory {
            name: "Comics & Graphic Novels".into(),
            description: "Full-script comic formats with PAGE/PANEL hierarchy, per-page lettering numbers, balloon types, and SFX.".into(),
            formats: vec![
                "fountain+comic-dc".into(),
                "fountain+comic-dh".into(),
                "fountain+comic-indie".into(),
            ],
        },
        FormatCategory {
            name: "Stage".into(),
            description: "US and UK stage play formats.".into(),
            formats: vec![
                "fountain+stage-us".into(),
                "fountain+stage-uk".into(),
            ],
        },
        FormatCategory {
            name: "Interactive".into(),
            description: "Branching dialogue and systemic voice-over for games.".into(),
            formats: vec![
                "fountain+branch".into(),
                "fountain+barks".into(),
            ],
        },
    ]
}
