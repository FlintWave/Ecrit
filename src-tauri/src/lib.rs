pub mod fountain;
pub mod project;

use pyo3::prelude::*;
use fountain::parser::FountainParser;
use fountain::dialect;
use project::manager::ProjectManager;

#[pyfunction]
fn parse_fountain(text: &str) -> PyResult<String> {
    let parser = FountainParser::new();
    let doc = parser.parse(text);
    Ok(serde_json::to_string(&doc).unwrap())
}

#[pyfunction]
fn get_script_stats(text: &str) -> PyResult<String> {
    let parser = FountainParser::new();
    let doc = parser.parse(text);
    let stats = parser.compute_stats(&doc);
    Ok(serde_json::to_string(&stats).unwrap())
}

#[pyfunction]
fn get_dialects() -> PyResult<String> {
    Ok(serde_json::to_string(&dialect::builtin_dialects()).unwrap())
}

#[pyfunction]
fn get_format_categories() -> PyResult<String> {
    Ok(serde_json::to_string(&dialect::format_categories()).unwrap())
}

#[pyfunction]
fn create_project(
    folder: &str,
    title: &str,
    author: &str,
    format_id: &str,
    paper: &str,
    kind: &str,
) -> PyResult<String> {
    let paper_size = match paper {
        "A4" => dialect::PaperSize::A4,
        _ => dialect::PaperSize::USLetter,
    };
    let project_kind = match kind {
        "Series" => project::types::ProjectKind::Series,
        _ => project::types::ProjectKind::Single,
    };
    match ProjectManager::create_project(folder, title, author, format_id, paper_size, project_kind) {
        Ok(meta) => Ok(serde_json::to_string(&meta).unwrap()),
        Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e)),
    }
}

#[pyfunction]
fn open_project(path: &str) -> PyResult<String> {
    match ProjectManager::open_project(path) {
        Ok(data) => Ok(serde_json::to_string(&data).unwrap()),
        Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e)),
    }
}

#[pyfunction]
fn save_script(path: &str, content: &str) -> PyResult<()> {
    ProjectManager::save_script(path, content)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
}

#[pyfunction]
fn list_projects(folder: &str) -> PyResult<String> {
    match ProjectManager::list_projects(folder) {
        Ok(projects) => Ok(serde_json::to_string(&projects).unwrap()),
        Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e)),
    }
}

#[pyfunction]
fn save_characters(path: &str, characters_json: &str) -> PyResult<()> {
    let characters: Vec<project::types::CharacterData> =
        serde_json::from_str(characters_json)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    ProjectManager::save_characters(path, &characters)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
}

#[pyfunction]
fn save_graph(path: &str, nodes_json: &str) -> PyResult<()> {
    let nodes: Vec<project::types::GraphNode> =
        serde_json::from_str(nodes_json)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    ProjectManager::save_graph(path, &nodes)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
}

#[pyfunction]
fn save_cover(path: &str, cover_json: &str) -> PyResult<()> {
    let cover: project::types::CoverData =
        serde_json::from_str(cover_json)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    ProjectManager::save_cover(path, &cover)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
}

#[pyfunction]
fn save_plan_document(path: &str, doc_id: &str, content: &str) -> PyResult<()> {
    ProjectManager::save_plan_document(path, doc_id, content)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
}

#[pymodule]
fn ecrit_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_fountain, m)?)?;
    m.add_function(wrap_pyfunction!(get_script_stats, m)?)?;
    m.add_function(wrap_pyfunction!(get_dialects, m)?)?;
    m.add_function(wrap_pyfunction!(get_format_categories, m)?)?;
    m.add_function(wrap_pyfunction!(create_project, m)?)?;
    m.add_function(wrap_pyfunction!(open_project, m)?)?;
    m.add_function(wrap_pyfunction!(save_script, m)?)?;
    m.add_function(wrap_pyfunction!(list_projects, m)?)?;
    m.add_function(wrap_pyfunction!(save_characters, m)?)?;
    m.add_function(wrap_pyfunction!(save_graph, m)?)?;
    m.add_function(wrap_pyfunction!(save_cover, m)?)?;
    m.add_function(wrap_pyfunction!(save_plan_document, m)?)?;
    Ok(())
}
