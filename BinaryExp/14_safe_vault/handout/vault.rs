// vault.rs — ordinary engineering :: vault-svc v2 (memory-safe rewrite)
//
// "v1 was C. v2 is Rust. Migration complete. No action required."
// Labels are a proper enum now, with an automation tier: promote a
// label to a callback and `run` will invoke it. The promotion is a
// one-byte tag flip through a raw pointer — faster than rebuilding
// the value, and safe because the index was bounds-checked.
// build: rustc -O -C strip=debuginfo --edition 2021 -o vault vault.rs

use std::fs;
use std::io::{Read, Write};

#[repr(u8)]
enum Label {
    Text([u8; 64]),
    Callback(fn()),
}

fn denied() {
    println!("access denied — auditors have been notified.");
}

/// Automation-tier callbacks available to enterprise tenants.
/// (The tier is not wired to provisioning yet.)
#[used]
static CALLBACKS: [fn(); 2] = [denied, print_flag];

fn print_flag() {
    for path in ["flag.txt", "/vuln/flag.txt"] {
        if let Ok(raw) = fs::read_to_string(path) {
            println!("{}", raw.trim());
            return;
        }
    }
    println!("flag file not found — ask the organizers");
}

fn hex_val(b: u8) -> Option<u8> {
    match b {
        b'0'..=b'9' => Some(b - b'0'),
        b'a'..=b'f' => Some(b - b'a' + 10),
        b'A'..=b'F' => Some(b - b'A' + 10),
        _ => None,
    }
}

fn parse_idx(arg: &[u8], len: usize) -> Option<usize> {
    std::str::from_utf8(arg).ok()?.trim().parse::<usize>().ok().filter(|&i| i < len)
}

/// Promote a stored text label to an automation callback.
///
/// The label index was bounds-checked by the caller, so the tag write
/// cannot go out of bounds. One byte, no revalidation needed.
fn promote_label(labels: &mut Vec<Label>, idx: usize) {
    unsafe {
        let tag = labels.as_mut_ptr().add(idx) as *mut u8;
        // Text = 0, Callback = 1: flip the tag in place.
        *tag = 1;
    }
    println!("label {} promoted to automation tier.", idx);
}

fn run_label(label: &Label) {
    match label {
        Label::Text(_) => println!("not a callback — promote it first."),
        Label::Callback(f) => f(),
    }
}

fn show_label(label: &Label) {
    match label {
        Label::Text(bytes) => {
            let end = bytes.iter().position(|&b| b == 0).unwrap_or(64);
            println!("label: {}", String::from_utf8_lossy(&bytes[..end]));
        }
        Label::Callback(_) => println!("callback redacted."),
    }
}

/// Raw line reader: one byte at a time, keeps embedded NULs.
fn read_line(stdin: &mut std::io::StdinLock, out: &mut Vec<u8>) -> bool {
    out.clear();
    let mut one = [0u8; 1];
    loop {
        match stdin.read(&mut one) {
            Ok(0) => return !out.is_empty(),
            Ok(_) => {
                if one[0] == b'\n' {
                    return true;
                }
                if one[0] == b'\r' {
                    continue;
                }
                if out.len() < 250 {
                    out.push(one[0]);
                }
            }
            Err(_) => return false,
        }
    }
}

fn main() {
    let stdout = std::io::stdout();
    let mut out = stdout.lock();
    let stdin = std::io::stdin();
    let mut input = stdin.lock();

    writeln!(out, "ordinary engineering — vault-svc v2 (memory-safe rewrite)").unwrap();
    writeln!(out, "labels with an automation tier. store one, promote it, run it.").unwrap();
    writeln!(out, "commands: store <hex> | promote <id> | run <id> | show <id> | info | quit").unwrap();
    writeln!(out, "ready.").unwrap();
    out.flush().unwrap();
    drop(out);

    // One session window per connection, like the C service's alarm(300).
    std::thread::spawn(|| {
        std::thread::sleep(std::time::Duration::from_secs(300));
        std::process::exit(0);
    });

    let mut labels: Vec<Label> = Vec::new();
    let mut line: Vec<u8> = Vec::with_capacity(256);
    loop {
        if !read_line(&mut input, &mut line) {
            break;
        }
        if line.len() >= 6 && &line[..6] == b"store " {
            let hex = &line[6..];
            if hex.len() > 128 || hex.len() % 2 != 0 {
                println!("bad label — hex, 64 bytes max.");
                continue;
            }
            let mut buf = [0u8; 64];
            let mut ok = true;
            for (i, pair) in hex.chunks(2).enumerate() {
                match (hex_val(pair[0]), hex_val(pair[1])) {
                    (Some(hi), Some(lo)) => buf[i] = hi << 4 | lo,
                    _ => {
                        ok = false;
                        break;
                    }
                }
            }
            if !ok {
                println!("bad label — hex, 64 bytes max.");
                continue;
            }
            labels.push(Label::Text(buf));
            println!("stored label {}.", labels.len() - 1);
        } else if line.len() >= 8 && &line[..8] == b"promote " {
            match parse_idx(&line[8..], labels.len()) {
                Some(i) => promote_label(&mut labels, i),
                None => println!("unknown label."),
            }
        } else if line.len() >= 4 && &line[..4] == b"run " {
            match parse_idx(&line[4..], labels.len()) {
                Some(i) => run_label(&labels[i]),
                None => println!("unknown label."),
            }
        } else if line.len() >= 5 && &line[..5] == b"show " {
            match parse_idx(&line[5..], labels.len()) {
                Some(i) => show_label(&labels[i]),
                None => println!("unknown label."),
            }
        } else if &line[..] == b"info" {
            println!(
                "build=v2.1.0-rust labels={} denied={:p} size={} tag_text=0 tag_callback=1",
                labels.len(),
                denied as *const (),
                std::mem::size_of::<Label>(),
            );
        } else if &line[..] == b"quit" {
            println!("bye");
            break;
        } else {
            println!("unknown command");
        }
    }
}
