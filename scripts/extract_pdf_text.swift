import Foundation
import PDFKit

let arguments = CommandLine.arguments
guard arguments.count == 2 else {
    fputs("usage: extract_pdf_text.swift FILE\n", stderr)
    exit(2)
}
let path = arguments[1]
guard let document = PDFDocument(url: URL(fileURLWithPath: path)) else {
    fputs("could not open PDF\n", stderr)
    exit(1)
}
for index in 0..<document.pageCount {
    guard let page = document.page(at: index), let text = page.string else { continue }
    print("\n--- PAGE \(index + 1) ---\n")
    print(text)
}
