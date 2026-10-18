export interface Point {
  x: number
  y: number
}

export interface Size {
  width: number
  height: number
}

export interface Box extends Point, Size {}

export interface Region extends Box {
  id: string
  radius: number
  rotation: number
}
