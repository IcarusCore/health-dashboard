// ImportPage.tsx
import { useCallback, useEffect, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import api from '../services/api';
import toast from 'react-hot-toast';
import { format } from 'date-fns';
import { ArrowUpTrayIcon, CheckCircleIcon, XCircleIcon, ClockIcon } from '@heroicons/react/24/outline';

export default function ImportPage() {
  const [uploads, setUploads] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    fetchImportHistory();
  }, []);

  const fetchImportHistory = async () => {
    try {
      const [history, summaryData] = await Promise.all([
        api.getImportHistory(),
        api.getImportSummary(),
      ]);
      setUploads(history);
      setSummary(summaryData);
    } catch (error) {
      console.error('Failed to fetch import history:', error);
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== 'xml' && ext !== 'zip') {
      toast.error('Please upload an export.xml or export.zip file');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      await api.uploadAppleHealth(file, (progress) => {
        setUploadProgress(progress);
      });
      toast.success('Import started! This may take several minutes.');
      fetchImportHistory();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Upload failed');
    } finally {
      setIsUploading(false);
      setUploadProgress(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/xml': ['.xml'],
      'application/zip': ['.zip'],
    },
    maxFiles: 1,
    disabled: isUploading,
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-success" />;
      case 'failed':
        return <XCircleIcon className="w-5 h-5 text-error" />;
      default:
        return <ClockIcon className="w-5 h-5 text-warning animate-pulse" />;
    }
  };

  return (
    <div className="space-y-6 animate-in">
      <h1 className="text-2xl font-bold text-dark-50">Import Data</h1>

      {/* Upload Zone */}
      <div
        {...getRootProps()}
        className={`card border-2 border-dashed cursor-pointer transition-all ${
          isDragActive
            ? 'border-primary-500 bg-primary-500/10'
            : 'border-dark-600 hover:border-primary-500/50'
        } ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input {...getInputProps()} />
        <div className="text-center py-8">
          <ArrowUpTrayIcon className="w-12 h-12 text-dark-400 mx-auto mb-4" />
          {isUploading ? (
            <div>
              <p className="text-dark-200 mb-2">Uploading...</p>
              <div className="w-48 mx-auto progress-bar">
                <div
                  className="progress-bar-fill bg-primary-500"
                  style={{ width: `${uploadProgress || 0}%` }}
                />
              </div>
              <p className="text-sm text-dark-400 mt-2">{uploadProgress}%</p>
            </div>
          ) : isDragActive ? (
            <p className="text-primary-400">Drop your Apple Health export here</p>
          ) : (
            <>
              <p className="text-dark-200 mb-2">Drag & drop your Apple Health export</p>
              <p className="text-sm text-dark-400">or click to browse (export.xml or export.zip)</p>
            </>
          )}
        </div>
      </div>

      {/* Instructions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-dark-100 mb-3">How to Export from Apple Health</h3>
        <ol className="space-y-2 text-dark-300">
          <li>1. Open the <strong>Health</strong> app on your iPhone</li>
          <li>2. Tap your profile picture in the top right</li>
          <li>3. Scroll down and tap <strong>Export All Health Data</strong></li>
          <li>4. Wait for the export to complete (may take several minutes)</li>
          <li>5. Save or share the export.zip file to your computer</li>
          <li>6. Upload the file here</li>
        </ol>
      </div>

      {/* Import Summary */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card text-center">
            <p className="text-2xl font-bold text-dark-50">{summary.total_measurements?.toLocaleString()}</p>
            <p className="text-sm text-dark-400">Measurements</p>
          </div>
          <div className="card text-center">
            <p className="text-2xl font-bold text-dark-50">{summary.total_workouts?.toLocaleString()}</p>
            <p className="text-sm text-dark-400">Workouts</p>
          </div>
          <div className="card text-center">
            <p className="text-2xl font-bold text-dark-50">{summary.total_sleep_sessions?.toLocaleString()}</p>
            <p className="text-sm text-dark-400">Sleep Sessions</p>
          </div>
          <div className="card text-center">
            <p className="text-2xl font-bold text-dark-50">{summary.successful_imports}</p>
            <p className="text-sm text-dark-400">Successful Imports</p>
          </div>
        </div>
      )}

      {/* Import History */}
      <div className="card">
        <h3 className="text-lg font-semibold text-dark-100 mb-4">Import History</h3>
        {uploads.length === 0 ? (
          <p className="text-dark-400 text-center py-4">No imports yet</p>
        ) : (
          <div className="space-y-3">
            {uploads.map((upload) => (
              <div key={upload.id} className="flex items-center gap-4 p-4 bg-dark-800 rounded-lg">
                {getStatusIcon(upload.status)}
                <div className="flex-1">
                  <p className="font-medium text-dark-100">{upload.filename}</p>
                  <p className="text-sm text-dark-400">
                    {format(new Date(upload.created_at), 'MMM d, yyyy • h:mm a')}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-dark-200">
                    {upload.records_imported?.toLocaleString()} records
                  </p>
                  <p className="text-xs text-dark-400 capitalize">{upload.status}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
