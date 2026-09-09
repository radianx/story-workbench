use std::collections::HashMap;
use keyring::{Entry, Error};
use serde_json::{json, Value};

pub const VOICE: &[&str] = &["openai", "gemini"];
pub const ENGINE: &[&str] = &["openai", "gemini", "anthropic", "deepseek", "kimi", "local"];
const UNAVAILABLE: &str = "No se pudo acceder al llavero del sistema. Desbloquealo o elegí uso solo en memoria.";

pub struct Vault {
    service: String,
    pub keys: HashMap<String, String>,
}
impl Vault {
    pub fn new(profile: &std::path::Path) -> Self {
        Self { service: format!("local.storyworkbench.desktop:{}", profile.display()), keys: HashMap::new() }
    }
    pub fn account(engine: bool, provider: &str) -> Result<String, &'static str> {
        if !(if engine {ENGINE} else {VOICE}).contains(&provider) {return Err("Proveedor inválido.")}
        Ok(format!("{}/{provider}", if engine {"engine"} else {"voice"}))
    }
    fn entry(&self, account: &str) -> Result<Entry, &'static str> {
        Entry::new(&self.service, account).map_err(|_| UNAVAILABLE)
    }
    pub fn load(&self, account: &str) -> Result<Option<String>, &'static str> {
        match self.entry(account)?.get_password() {
            Ok(key) if !key.is_empty() && key.len()<=2048 => Ok(Some(key)),
            Err(Error::NoEntry) => Ok(None),
            _ => Err(UNAVAILABLE), // Nunca propagar errores del llavero: pueden contener bytes del secreto.
        }
    }
    pub fn status(&self, engine: bool) -> Value {
        let mut stored=serde_json::Map::new();let mut available=true;
        for provider in if engine {ENGINE} else {VOICE} {
            match self.load(&Self::account(engine,provider).unwrap()) {
                Ok(key) => {stored.insert((*provider).into(),json!(key.is_some()));},
                Err(_) => {available=false;stored.insert((*provider).into(),Value::Null);},
            }
        }
        json!({"available":available,"stored":stored,"reason":if available {"Guardada en el llavero del sistema, separada de tus proyectos."} else {UNAVAILABLE}})
    }
    pub fn save(&self, account: &str, remember: bool) -> Result<(), &'static str> {
        let entry=self.entry(account)?;
        if remember {
            let key=self.keys.get(account).filter(|key|!key.is_empty()).ok_or("Ingresá la clave antes de recordarla.")?;
            entry.set_password(key).map_err(|_|"La clave está en memoria, pero no se pudo guardar en el llavero.")
        } else {
            match entry.delete_credential() {
                Ok(()) | Err(Error::NoEntry) => Ok(()),
                Err(_) => Err("No se pudo borrar la clave guardada. Desbloqueá el llavero y volvé a intentar."),
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn providers_are_separate_and_bounded() {
        assert_ne!(Vault::account(true,"gemini").unwrap(),Vault::account(false,"gemini").unwrap());
        assert!(Vault::account(false,"anthropic").is_err());
        for value in ["", "../openai", "OPENAI", "unknown"] {assert!(Vault::account(true,value).is_err());}
    }
}
