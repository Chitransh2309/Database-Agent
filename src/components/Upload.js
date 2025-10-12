import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import styled from "styled-components";
import { X, FileText, Archive } from "lucide-react"; // Importing File Icons
import Footer from "./Footer";
import Loader from "./Loader";


const Container = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 90vh;
  gap: 100px;
`;

const Heading = styled.h1`
  font-size: 70px;
  color: white;
  text-align: center;
  font-weight: bold;
  margin-top: -50px;
`;

const ContentWrapper = styled.div`
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 50px;
  margin-top: -20px;
`;

const FileUploadContainer = styled.div`
  width: 450px;
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const FileUploadBox = styled.div`
  border: 3px dashed #b8bcbf;
  border-radius: 15px;
  padding: 40px;
  text-align: center;
  background-color: rgba(9, 9, 9, 0.963);
  transition: background-color 0.3s ease-in-out;
  cursor: pointer;
  font-size: 20px;
  font-weight: bold;
  color: white;

  &.dragover {
    background-color: #007bff;
    color: white;
  }
`;

const PreviewWrapper = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
`;

const PreviewFileContainer = styled.div`
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
`;

const RemoveButton = styled.button`
  position: absolute;
  top: -8px;
  right: -8px;
  background: red;
  border: none;
  color: white;
  border-radius: 50%;
  width: 25px;
  height: 25px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
  transition: 0.2s ease-in-out;

  &:hover {
    background: white;
    color: red;
  }
`;

const PreviewImage = styled.img`
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 10px;
  border: 2px solid #007bff;
`;

const CsvFileIcon = styled(FileText)`
  width: 60px;
  height: 60px;
  color: #007bff;
`;

const ZipFileIcon = styled(Archive)`
  width: 60px;
  height: 60px;
  color: #ff9800;
`;
const ButtonContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 10px;
  `;
const UploadButton = styled.button`
  background-color: #007bff;
  color: white;
  padding: 12px 30px;
  font-size: 18px;
  border: none;
  border-radius: 10px;
  margin-top: 15px;
  cursor: pointer;
  transition: 0.3s ease-in-out;

  &:hover {
    background-color: #0056b3;
  }
`;

const Upload = () => {
  const [files, setFiles] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    if (rejectedFiles.length > 0) {
      setError("Only .pdf files are allowed!");
      return;
    }

    setError(""); // Clear any previous errors

    const newFiles = acceptedFiles.map(file =>
      Object.assign(file, { preview: file.type.startsWith("image") ? URL.createObjectURL(file) : null })
    );
    setFiles(prevFiles => [...prevFiles, ...newFiles]);
  }, []);

  const removeFile = (index) => {
    const newFiles = [...files];
    newFiles.splice(index, 1);
    setFiles(newFiles);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": []
    }
    
  });

  // const uploadFiles = async () => {
  //   if (files.length === 0) {
  //     alert("No files selected!");
  //     return;
  //   }
  
  //   const formData = new FormData();
  //   files.forEach(file => formData.append("files", file));
  
  //   try {
  //     const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/upload`, {
  //       method: "POST",
  //       body: formData,
  //     });
  
  //     if (response.ok) {
  //       alert("Files uploaded successfully");
  //        // Clear uploaded files after success
  //     } else {
  //       console.error("Upload failed");
  //     }
  //   } catch (error) {
  //     console.error("Upload error:", error);
  //   }
  // };
  
  const mergeFiles = async () => {
    if (files.length === 0) {
      alert("No files selected!");
      return;
    }
  
    const formData = new FormData();
    files.forEach(file => formData.append("files", file));
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/upload/merge`, {
        method: "POST",
        body: formData,
      });
  
      const data = await response.json();
  
      if (response.ok) {
        alert("PDFs merged successfully!");
        setFiles([]);
        window.open(data.mergedFile, "_blank");
      } else {
        console.error("Merge failed:", data.error);
      }
    } catch (error) {
      console.error("Merge error:", error);
    } finally {
      setLoading(false);
    }
  };
  
  const compressFile = async () => {
    if (files.length === 0) {
      alert("No files selected!");
      return;
    }
  
    const formData = new FormData();
    files.forEach(file => formData.append("files", file));
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/upload/compress`, {
        method: "POST",
        body: formData,
      });
  
      const data = await response.json();
  
      if (response.ok) {
        alert("PDF compressed successfully!");
        setFiles([]);
        window.open(data.compressedFile, "_blank");
      } else {
        console.error("Compression failed:", data.error);
      }
    } catch (error) {
      console.error("Compression error:", error);
    }finally {
      setLoading(false);
    }
  };
  
  const redactFile = async () => {
    if (files.length === 0) {
      alert("No files selected!");
      return;
    }
  
    const formData = new FormData();
    files.forEach(file => formData.append("files", file));
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/upload/redact`, {
        method: "POST",
        body: formData,
      });
  
      const data = await response.json();
  
      if (response.ok) {
        alert("PDF redacted successfully!");
        setFiles([]);
        window.open(data.redactFile, "_blank");
      } else {
        console.error("Redact failed:", data.error);
      }
    } catch (error) {
      console.error("Redact error:", error);
    }finally {
      setLoading(false);
    }
  };
  
  const flattenFile = async () => {
    if (files.length === 0) {
      alert("No files selected!");
      return;
    }
  
    const formData = new FormData();
    files.forEach(file => formData.append("files", file));
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/upload/flatten`, {
        method: "POST",
        body: formData,
      });
  
      const data = await response.json();
  
      if (response.ok) {
        alert("PDF flattened successfully!");
        setFiles([]);
        window.open(data.flattenFile, "_blank");
      } else {
        console.error("flatten failed:", data.error);
      }
    } catch (error) {
      console.error("flatten error:", error);
    }finally {
      setLoading(false);
    }
  };

  return (
    <Container>
      {loading && <Loader />}
      <Heading>Upload Files</Heading>
      <ContentWrapper>
        <FileUploadContainer>
          <FileUploadBox {...getRootProps()} className={isDragActive ? "dragover" : ""}>
            <input {...getInputProps()} />
            <p>Drag & Drop your files here or click to upload</p>
            <span className="text-danger">(*Only .pdf accepted)</span>
          </FileUploadBox>

          {error && <p style={{ color: "red", marginTop: "10px" }}>{error}</p>}
          <ButtonContainer>
            {/* <UploadButton onClick={uploadFiles}>Upload</UploadButton> */}
            <UploadButton onClick={mergeFiles}>Merge PDFs</UploadButton>
            <UploadButton onClick={compressFile}>Compress PDF</UploadButton>
            <UploadButton onClick={redactFile}>Redact PDF</UploadButton>
            <UploadButton onClick={flattenFile}>Flatten PDF</UploadButton>
          </ButtonContainer>
        </FileUploadContainer>

        {files.length > 0 && (
          <PreviewWrapper>
            {files.map((file, index) => (
              <PreviewFileContainer key={index}>
                <RemoveButton onClick={() => removeFile(index)}>
                  <X size={14} />
                </RemoveButton>
                {file.preview ? (
                  <PreviewImage src={file.preview} alt="preview" />
                ) : file.name.endsWith(".pdf") ? (
                  <>
                    <CsvFileIcon />
                    <p style={{ color: "white", fontSize: "14px", marginTop: "5px" }}>
                      {file.name}
                    </p>
                  </>
                ) : file.name.endsWith(".zip") || file.name.endsWith(".rar") ? (
                  <>
                    <ZipFileIcon />
                    <p style={{ color: "white", fontSize: "14px", marginTop: "5px" }}>
                      {file.name}
                    </p>
                  </>
                ) : null}
              </PreviewFileContainer>
            ))}
          </PreviewWrapper>
        )}
      </ContentWrapper>
      <Footer/>
    </Container>
    
  );
};

export default Upload;
