import manual from './sidebar.json'
import aimdk from './aimdk-sidebar.json'

/** Merged navigation: product manuals + AimDK (`en` / `zh` with optional `basePath`). */
const allSidebars = { ...manual, ...aimdk }

export default allSidebars
