import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import crypto from 'node:crypto';
import AdmZip from 'adm-zip';

const root = fileURLToPath(new URL('../', import.meta.url));

export async function packageBlenderAddon() {
	const source = path.join(root, 'addons/blender/io_scene_wowobj');
	const manifest = await fs.readFile(path.join(source, '__init__.py'), 'utf8');
	const match = manifest.match(/'version':\s*\((\d+),\s*(\d+),\s*(\d+)\)/);
	if (!match) throw new Error('Cannot read Blender addon version');
	const version = match.slice(1).join('.');
	const zip = new AdmZip();
	const files = (await fs.readdir(source, { withFileTypes: true }))
		.filter(entry => entry.isFile() && /\.(py|png|txt|dll)$/i.test(entry.name))
		.map(entry => entry.name).sort();
	for (const required of ['__init__.py', 'import_wowobj.py', 'import_session.py',
		'diagnostics.py', 'navigation_export.py', 'navigation_import.py',
		'navigation_liquids.py', 'view_settings.py', 'import_names.py',
		'animation_processor.py', 'native_geometry.py', 'README.txt', 'logo.png']) {
		if (!files.includes(required)) throw new Error(`Missing addon file: ${required}`);
	}
	for (const file of files) zip.addLocalFile(path.join(source, file), 'io_scene_wowobj');
	const canonical = path.join(root, 'addons/blender/io_scene_wowobj.zip');
	await zip.writeZipPromise(canonical);
	const output = path.join(root, 'publish/blender-addon');
	await fs.mkdir(output, { recursive: true });
	const name = `io_scene_wowobj-${version}.zip`;
	await fs.copyFile(canonical, path.join(output, name));
	const hash = crypto.createHash('sha256').update(await fs.readFile(canonical)).digest('hex');
	await fs.writeFile(path.join(output, 'SHA256SUMS.txt'), `${hash}  ${name}\n`);
	console.log(`Blender addon ${version}: ${files.length} files -> publish/blender-addon/${name}`);
	return { version, files, name, hash };
}

if (import.meta.main) await packageBlenderAddon();
