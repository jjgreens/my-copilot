import path, { dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const ROOT_FOLDER = path.join(__dirname, "..");
const AGENTS_DIR = path.join(ROOT_FOLDER, "agents");
const SKILLS_DIR = path.join(ROOT_FOLDER, "skills");
const INSTRUCTIONS_DIR = path.join(ROOT_FOLDER, "instructions");
const PLUGINS_DIR = path.join(ROOT_FOLDER, "plugins");

export { AGENTS_DIR, INSTRUCTIONS_DIR, PLUGINS_DIR, ROOT_FOLDER, SKILLS_DIR };
